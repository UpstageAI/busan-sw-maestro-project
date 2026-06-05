"""data/raw/*.md + data/embeddings/*.npy 를 ChromaDB 에 적재한다.

크롤링 파이프라인(embed.py) 결과물을 대상으로 한다.
- .npy 가 1D 배열이면 문서 단위 단일 벡터로 처리
- .npy 가 2D 배열이면 행(row) 단위 청크로 처리

사용법:
    python -m src.ingest_crawl
    python -m src.ingest_crawl --reset
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import numpy as np
import chromadb

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "사다리타기 문서 인덱스 - 사다리타기 문서 인덱스.csv"
RAW_DIR = ROOT / "data" / "raw"
EMB_DIR = ROOT / "data" / "embeddings"


def _slugify(title: str) -> str:
    title = re.sub(r"[\[\]()【】『』「」《》<>]", "", title)
    title = re.sub(r"\s+", "_", title.strip())
    title = re.sub(r"[^\w가-힣-]", "", title)
    return title[:60]


def _load_source_urls() -> dict[str, str]:
    if not CSV_PATH.exists():
        return {}

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = csv.DictReader(f)
        return {
            _slugify(row["문서 제목"]): (row.get("수집 채널") or "").strip()
            for row in rows
            if row.get("문서 제목")
        }


def _replace_original_url(doc_text: str, source_url: str) -> str:
    if not source_url:
        return doc_text

    lines = doc_text.split("\n")
    for idx, line in enumerate(lines[:8]):
        if line.strip().startswith("원문:"):
            lines[idx] = f"원문: {source_url}"
            return "\n".join(lines)

    if lines and lines[0].startswith("#"):
        lines.insert(1, "")
        lines.insert(2, f"원문: {source_url}")
        return "\n".join(lines)

    return f"원문: {source_url}\n\n{doc_text}"


def ingest(reset: bool = False) -> None:
    from .config import get_settings
    s = get_settings()
    source_urls = _load_source_urls()

    client = chromadb.PersistentClient(path=s.chroma_path)

    if reset:
        try:
            client.delete_collection(s.chroma_collection)
            print(f"기존 컬렉션 '{s.chroma_collection}' 삭제")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        s.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )

    npy_files = sorted(EMB_DIR.glob("*.npy"))
    if not npy_files:
        sys.exit(f"data/embeddings/ 에 .npy 파일이 없습니다. setup_data.py 를 먼저 실행하세요.")

    total = 0
    for npy_path in npy_files:
        name = npy_path.stem
        md_path = RAW_DIR / f"{name}.md"
        txt_path = RAW_DIR / f"{name}.txt"

        doc_text = ""
        for path in [md_path, txt_path]:
            if path.exists():
                for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
                    try:
                        doc_text = path.read_text(encoding=enc)
                        break
                    except UnicodeDecodeError:
                        continue
                break
        else:
            print(f"  ! {name}: 원문 파일 없음 — 건너뜀")
            continue

        source_url = source_urls.get(name, "")
        doc_text = _replace_original_url(doc_text, source_url)
        vectors = np.load(npy_path)
        if vectors.size == 0:
            print(f"  ! {name}: 빈 벡터 배열 — 건너뜀")
            continue

        metadata = {"source": name}
        if source_url:
            metadata["url"] = source_url

        if vectors.ndim == 1:
            # 단일 벡터: 문서 전체를 하나의 청크로
            collection.upsert(
                ids=[name],
                documents=[doc_text],
                embeddings=[vectors.tolist()],
                metadatas=[metadata],
            )
            total += 1
        else:
            # 다중 벡터: 행(row)마다 청크 분리
            lines = [l for l in doc_text.split("\n") if l.strip()]
            chunk_size = max(1, len(lines) // len(vectors))
            ids, docs, embs, metas = [], [], [], []
            for i, vec in enumerate(vectors):
                chunk_lines = lines[i * chunk_size:(i + 1) * chunk_size]
                chunk_text = "\n".join(chunk_lines) if chunk_lines else doc_text
                ids.append(f"{name}_{i}")
                docs.append(chunk_text)
                embs.append(vec.tolist())
                metas.append({**metadata, "chunk": i})
            collection.upsert(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
            total += len(vectors)

        print(f"  OK {name}")

    print(f"\n완료: 총 {total}개 항목 → {s.chroma_path}/{s.chroma_collection}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    ingest(reset=args.reset)


if __name__ == "__main__":
    main()

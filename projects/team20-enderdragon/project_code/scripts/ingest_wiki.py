"""마인크래프트 위키(Obsidian vault) 마크다운을 Qdrant에 적재한다.

사용 예:
  uv run python scripts/ingest_wiki.py --limit 50    # 시범 적재(속도 보정)
  uv run python scripts/ingest_wiki.py               # 전체 적재

소스 경로: --source 인자 또는 WIKI_VAULT_PATH 환경변수
대상 Qdrant: QDRANT_URL(공유 클라우드) 또는 QDRANT_HOST/PORT(로컬)
"""
import argparse
import re
import sys
import time
import uuid
from pathlib import Path

import frontmatter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import models

# scripts/에서 app 패키지를 import할 수 있도록 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import QDRANT_COLLECTION, WIKI_VAULT_PATH  # noqa: E402
from app.core.vector_db import get_qdrant_client  # noqa: E402
from app.core.embedding import embed_documents, embedding_dim  # noqa: E402

# 적재 제외 디렉토리 (인덱스/메타/파이프라인/버전관리/도구상태)
EXCLUDE_DIRS = {"00-인덱스", "_meta", "_pipeline", ".git", ".obsidian", ".omc"}

WIKILINK_LABELED = re.compile(r"\[\[[^\]|]+\|([^\]]+)\]\]")  # [[대상|표기]] -> 표기
WIKILINK_PLAIN = re.compile(r"\[\[([^\]]+)\]\]")             # [[대상]]    -> 대상
REPEAT_TOKEN = re.compile(r"(\S+)(?: \1){3,}")              # 반복 토큰(제작표 노이즈) 압축

MAX_DOC_CHARS = 20000  # 초대형 페이지 상한
_UUID_NS = uuid.UUID("00000000-0000-0000-0000-0000000a5d10")


def clean_body(text: str) -> str:
    text = WIKILINK_LABELED.sub(r"\1", text)
    text = WIKILINK_PLAIN.sub(r"\1", text)
    text = REPEAT_TOKEN.sub(r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def iter_markdown(root: Path):
    for p in sorted(root.rglob("*.md")):
        if set(p.relative_to(root).parts) & EXCLUDE_DIRS:
            continue
        yield p


def point_id(rel_path: str, idx: int) -> str:
    """경로+청크번호로 안정적인 UUID 생성 → 재실행 시 멱등 upsert."""
    return str(uuid.uuid5(_UUID_NS, f"{rel_path}::{idx}"))


def _as_csv(value) -> str:
    if isinstance(value, list):
        return ",".join(str(v) for v in value)
    return str(value) if value else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=WIKI_VAULT_PATH, help="위키 vault 경로")
    ap.add_argument("--limit", type=int, default=0, help="처리할 md 파일 수 (0=전체)")
    ap.add_argument("--batch", type=int, default=64, help="임베딩 배치 크기")
    args = ap.parse_args()

    if not args.source:
        sys.exit("WIKI_VAULT_PATH(또는 --source)가 필요합니다.")
    root = Path(args.source).expanduser()
    if not root.is_dir():
        sys.exit(f"소스 경로를 찾을 수 없습니다: {root}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )

    client = get_qdrant_client()
    dim = embedding_dim()
    if QDRANT_COLLECTION not in {c.name for c in client.get_collections().collections}:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

    files = list(iter_markdown(root))
    if args.limit:
        files = files[: args.limit]
    print(f"[ingest] 대상 파일 {len(files)}개 · 임베딩 차원 {dim} · 컬렉션 '{QDRANT_COLLECTION}'")

    # 1) 청크 생성
    chunks: list[tuple[str, dict]] = []  # (point_id, payload)
    for p in files:
        rel = str(p.relative_to(root))
        try:
            post = frontmatter.load(p)
        except Exception:
            continue
        meta = post.metadata or {}
        body = clean_body(post.content)[:MAX_DOC_CHARS]
        if not body:
            continue
        title = meta.get("title") or p.stem
        for i, ck in enumerate(splitter.split_text(body)):
            payload = {
                "content": f"# {title}\n{ck}",
                "title": title,
                "category": _as_csv(meta.get("categories")),
                "mc_edition": _as_csv(meta.get("mc_edition")),
                "source_url": meta.get("source_url", ""),
                "rel_path": rel,
                "chunk_index": i,
            }
            chunks.append((point_id(rel, i), payload))

    print(f"[ingest] 총 청크 {len(chunks)}개")
    if not chunks:
        return

    # 2) 배치 임베딩 + upsert (진행률·ETA 출력 → 시범 적재로 전체 시간 환산)
    t0 = time.time()
    done = 0
    for s in range(0, len(chunks), args.batch):
        batch = chunks[s : s + args.batch]
        vectors = embed_documents([pl["content"] for _, pl in batch])
        points = [
            models.PointStruct(id=pid, vector=vec, payload=pl)
            for (pid, pl), vec in zip(batch, vectors)
        ]
        client.upsert(collection_name=QDRANT_COLLECTION, points=points)
        done += len(batch)
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed else 0
        eta = (len(chunks) - done) / rate if rate else 0
        print(f"  {done}/{len(chunks)}  ({rate:.1f} chunk/s, ETA {eta:.0f}s)")

    print(f"[ingest] 완료: {done}청크, {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

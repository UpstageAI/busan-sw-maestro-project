"""Google Drive 링크에서 문서 및 임베딩 파일을 다운로드한다.

사용법:
    python scripts/setup_data.py              # 임베딩 + 원문 모두 다운로드
    python scripts/setup_data.py --emb-only   # 임베딩만 다운로드
    python scripts/setup_data.py --raw-only   # 원문만 다운로드
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import gdown
except ImportError:
    sys.exit("gdown이 없습니다. pip install gdown 을 먼저 실행하세요.")

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "사다리타기 문서 인덱스 - 사다리타기 문서 인덱스.csv"
RAW_DIR = ROOT / "data" / "raw"
EMB_DIR = ROOT / "data" / "embeddings"


def extract_file_id(url: str) -> str | None:
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else None


def slugify(title: str) -> str:
    title = re.sub(r"[\[\]()【】『』「」《》<>]", "", title)
    title = re.sub(r"\s+", "_", title.strip())
    title = re.sub(r"[^\w가-힣-]", "", title)
    return title[:60]


def load_index() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def download_embeddings(rows: list[dict]) -> None:
    EMB_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[임베딩] {len(rows)}개 파일 다운로드 → {EMB_DIR}")
    for row in rows:
        url = row.get("임베딩 링크", "").strip()
        file_id = extract_file_id(url)
        if not file_id:
            print(f"  ! 링크 없음: {row['문서 제목'][:30]}")
            continue
        name = slugify(row["문서 제목"])
        out_path = EMB_DIR / f"{name}.npy"
        if out_path.exists():
            print(f"  - 이미 있음: {out_path.name}")
            continue
        print(f"  ↓ {name}")
        gdown.download(id=file_id, output=str(out_path), quiet=True)


def download_raw(rows: list[dict]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[원문] {len(rows)}개 파일 다운로드 → {RAW_DIR}")
    for row in rows:
        url = row.get("원문 폴더의 문서 링크", "").strip()
        file_id = extract_file_id(url)
        if not file_id:
            print(f"  ! 링크 없음: {row['문서 제목'][:30]}")
            continue
        name = slugify(row["문서 제목"])
        out_path = RAW_DIR / f"{name}.md"
        if out_path.exists():
            print(f"  - 이미 있음: {out_path.name}")
            continue
        print(f"  ↓ {name}")
        gdown.download(id=file_id, output=str(out_path), quiet=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emb-only", action="store_true")
    parser.add_argument("--raw-only", action="store_true")
    args = parser.parse_args()

    rows = load_index()
    print(f"CSV 로드: {len(rows)}개 문서")

    if not args.raw_only:
        download_embeddings(rows)
    if not args.emb_only:
        download_raw(rows)

    print("\n완료. 다음 단계: python -m src.ingest_chroma")


if __name__ == "__main__":
    main()

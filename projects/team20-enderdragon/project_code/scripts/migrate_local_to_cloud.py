"""로컬 Qdrant의 벡터를 공유 Qdrant Cloud로 복사한다(재임베딩 없음).

기존에 로컬 docker Qdrant에 적재된 포인트(벡터+페이로드)를 그대로 scroll로 읽어
클라우드 컬렉션에 upsert한다. 포인트 ID가 동일하므로 멱등(재실행 안전)이다.
재임베딩을 하지 않으므로 비용이 들지 않고 vault 없이도 동작한다.

사용 예:
  # .env에 QDRANT_URL / QDRANT_API_KEY를 채운 뒤
  uv run python scripts/migrate_local_to_cloud.py

  # 또는 인자로 직접 지정
  uv run python scripts/migrate_local_to_cloud.py \
      --dst-url https://xxxx.cloud.qdrant.io:6333 --dst-api-key <KEY>

소스(로컬): --src-host/--src-port 또는 QDRANT_HOST/QDRANT_PORT (기본 localhost:6333)
대상(클라우드): --dst-url/--dst-api-key 또는 QDRANT_URL/QDRANT_API_KEY
"""
import argparse
import sys
import time
from pathlib import Path

from qdrant_client import QdrantClient, models

# scripts/에서 app 패키지를 import할 수 있도록 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import (  # noqa: E402
    QDRANT_COLLECTION,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_URL,
    QDRANT_API_KEY,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-host", default=QDRANT_HOST, help="로컬 Qdrant 호스트")
    ap.add_argument("--src-port", type=int, default=QDRANT_PORT, help="로컬 Qdrant 포트")
    ap.add_argument("--dst-url", default=QDRANT_URL, help="클라우드 Qdrant URL")
    ap.add_argument("--dst-api-key", default=QDRANT_API_KEY, help="클라우드 Qdrant API 키")
    ap.add_argument("--collection", default=QDRANT_COLLECTION, help="컬렉션 이름")
    ap.add_argument("--batch", type=int, default=64, help="scroll/upsert 배치 크기")
    ap.add_argument("--timeout", type=int, default=120, help="HTTP 타임아웃(초) — 클라우드 업로드용")
    args = ap.parse_args()

    if not args.dst_url:
        sys.exit("대상 클라우드 URL이 필요합니다(--dst-url 또는 .env의 QDRANT_URL).")

    coll = args.collection
    src = QdrantClient(host=args.src_host, port=args.src_port, timeout=args.timeout)
    dst = QdrantClient(url=args.dst_url, api_key=args.dst_api_key or None, timeout=args.timeout)

    # 1) 소스 컬렉션 파라미터 그대로 복제 (차원/거리)
    src_info = src.get_collection(coll)
    vectors_cfg = src_info.config.params.vectors  # 단일(무명) 벡터 설정
    size = vectors_cfg.size
    distance = vectors_cfg.distance
    src_count = src.count(coll, exact=True).count
    print(f"[migrate] 소스 '{coll}' @ {args.src_host}:{args.src_port} "
          f"— {src_count}포인트 · {size}차원 · {distance}")

    existing = {c.name for c in dst.get_collections().collections}
    if coll not in existing:
        dst.create_collection(
            collection_name=coll,
            vectors_config=models.VectorParams(size=size, distance=distance),
        )
        print(f"[migrate] 대상에 컬렉션 '{coll}' 생성됨")
    else:
        dst_existing = dst.count(coll, exact=True).count
        print(f"[migrate] 대상에 컬렉션 '{coll}' 이미 존재(현재 {dst_existing}포인트, 멱등 upsert 진행)")

    # 2) scroll로 벡터+페이로드 읽어 그대로 upsert
    t0 = time.time()
    offset = None
    done = 0
    while True:
        points, offset = src.scroll(
            collection_name=coll,
            limit=args.batch,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not points:
            break
        batch_points = [
            models.PointStruct(id=p.id, vector=p.vector, payload=p.payload)
            for p in points
        ]
        # 네트워크 일시 오류(타임아웃 등) 대비 배치 재시도. 멱등이라 재전송 안전.
        for attempt in range(1, 4):
            try:
                dst.upsert(collection_name=coll, points=batch_points)
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"  ! upsert 실패(시도 {attempt}/3): {type(e).__name__} — {2 * attempt}s 후 재시도")
                time.sleep(2 * attempt)
        done += len(points)
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed else 0
        print(f"  {done}/{src_count}  ({rate:.0f} pt/s)")
        if offset is None:
            break

    # 3) 검증: 대상 포인트 수가 소스와 일치하는지
    dst_count = dst.count(coll, exact=True).count
    ok = "OK" if dst_count == src_count else "불일치!"
    print(f"[migrate] 완료: 대상 {dst_count}포인트 / 소스 {src_count}포인트 [{ok}] "
          f"({time.time() - t0:.1f}s)")
    if dst_count != src_count:
        sys.exit(1)


if __name__ == "__main__":
    main()

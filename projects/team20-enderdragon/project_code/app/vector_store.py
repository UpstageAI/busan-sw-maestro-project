"""Qdrant 기반 벡터 스토어.

검색 인터페이스(search_documents)는 기존(ChromaDB) 시그니처를 유지하므로
agents/retrieval.py 등 호출부는 수정 없이 동작한다.
대량 적재는 scripts/ingest_wiki.py가 담당한다.
"""
from qdrant_client import models

from app.core.config import QDRANT_COLLECTION
from app.core.vector_db import get_qdrant_client
from app.core.embedding import embed_query, embedding_dim


def _collection_exists() -> bool:
    client = get_qdrant_client()
    return QDRANT_COLLECTION in {c.name for c in client.get_collections().collections}


def ensure_collection(dim: int | None = None) -> None:
    """컬렉션이 없으면 생성한다 (Cosine, 차원은 임베딩 모델 기준).

    주의: dim 미지정 시 임베딩 API를 호출하므로 UPSTAGE_API_KEY가 필요하다.
    """
    client = get_qdrant_client()
    if _collection_exists():
        return
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=dim or embedding_dim(),
            distance=models.Distance.COSINE,
        ),
    )


def search_documents(query: str, n_results: int = 3) -> list[dict]:
    """query와 유사한 문서를 Qdrant에서 검색한다. 반환 형태는 기존과 동일하다.

    [{"content": str, "metadata": dict, "distance": float}, ...]
    (distance에는 Qdrant 유사도 score가 담긴다 — 높을수록 유사)
    """
    if not _collection_exists():
        return []
    client = get_qdrant_client()
    vector = embed_query(query)
    hits = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=vector,
        limit=n_results,
        with_payload=True,
    ).points
    documents = []
    for h in hits:
        payload = h.payload or {}
        documents.append({
            "content": payload.get("content", ""),
            "metadata": {k: v for k, v in payload.items() if k != "content"},
            "distance": h.score,
        })
    return documents

"""Upstage Solar 임베딩을 이용해 관광지 후보를 의미 기반으로 검색하는 툴."""

from __future__ import annotations

import math
from typing import List

from langchain_upstage import UpstageEmbeddings

_spot_embeddings_cache: list[list[float]] = []
_cached_spots: list[dict] = []


def _spot_text(spot: dict) -> str:
    """스팟 딕셔너리를 임베딩 입력 텍스트로 변환."""
    name = spot.get("name", "")
    region = spot.get("region", "")
    spot_type = spot.get("type", "")
    mood = spot.get("mood", [])
    best_for = spot.get("best_for", [])
    return f"{name} {region} {spot_type} {' '.join(mood)} {' '.join(best_for)}"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도를 계산한다. 분모가 0이면 0.0 반환."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    denom = norm_a * norm_b
    if denom == 0.0:
        return 0.0
    return dot / denom


def get_top_k_spots(user_query: str, spots: list[dict], k: int = 15) -> list[dict]:
    """user_query와 코사인 유사도가 높은 상위 k개 관광지를 반환한다.

    Args:
        user_query: 사용자의 자연어 질의.
        spots: 검색 대상 관광지 딕셔너리 리스트.
        k: 반환할 최대 후보 수.

    Returns:
        유사도 내림차순으로 정렬된 상위 k개 관광지 리스트.
        실패 시 spots 전체를 반환한다.
    """
    global _spot_embeddings_cache, _cached_spots

    if not spots:
        return spots

    try:
        # spots 목록이 바뀐 경우(길이 변경) 재계산
        if len(_spot_embeddings_cache) != len(spots):
            texts = [_spot_text(spot) for spot in spots]
            passage_embedder = UpstageEmbeddings(model="solar-embedding-1-large-passage")
            _spot_embeddings_cache = passage_embedder.embed_documents(texts)
            _cached_spots = list(spots)

        query_embedder = UpstageEmbeddings(model="solar-embedding-1-large-query")
        query_vector: List[float] = query_embedder.embed_query(user_query)

        scored = [
            (spot, _cosine_similarity(query_vector, emb))
            for spot, emb in zip(spots, _spot_embeddings_cache)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [spot for spot, _ in scored[:k]]

    except Exception:
        return spots

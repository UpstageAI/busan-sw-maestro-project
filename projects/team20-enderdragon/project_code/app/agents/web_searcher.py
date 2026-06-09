"""web_search 노드 — RAG 커버리지가 부족할 때만 외부 검색으로 근거를 보강한다.

retrieve 다음에 실행된다. RAG(Qdrant) 결과가 충분하면(최고 유사도가 임계값 이상)
아무 일도 하지 않는다. 부족하면 **키 없는 마크 위키 검색**으로 보강하고, 비었고
Tavily 키가 있으면 일반 웹으로 한 번 더 폴백한다(best-effort). 결과는 기존
search_results 뒤에 병합해 코치가 더 풍부한 근거로 답하게 한다.
"""
import logging

from app.schemas import AgentState
from app.core.config import TAVILY_API_KEY, WEB_SEARCH_MIN_SCORE
from app.web_search import wiki_search, tavily_search

logger = logging.getLogger(__name__)


def _needs_web(results: list[dict], min_score: float) -> bool:
    """RAG 검색이 빈약한지 판정한다(결과 없음 또는 최고 유사도가 임계값 미만)."""
    if not results:
        return True
    best = max((r.get("distance", 0.0) for r in results), default=0.0)
    return best < min_score


def search_web(state: AgentState) -> dict:
    """커버리지 부족 시 위키(키리스) 우선, 비면 Tavily(키 있을 때)로 보강한다."""
    results = state.get("search_results", [])
    if not _needs_web(results, WEB_SEARCH_MIN_SCORE):
        return {}

    keywords = state.get("query_analysis", {}).get("keywords", [])
    query = f"{state.get('query', '')} {' '.join(keywords)}".strip()

    # 1) 키 없이 마크 위키 검색(기본)
    web = wiki_search(query, max_results=3)
    # 2) 위키가 비었고 Tavily 키가 있으면 일반 웹으로 폴백
    if not web and TAVILY_API_KEY:
        web = tavily_search(f"마인크래프트 {query}", max_results=3)
    if not web:
        return {}

    logger.info("WEB_SEARCH: 커버리지 보강 — 외부 결과 %d건 병합", len(web))
    return {"search_results": results + web}

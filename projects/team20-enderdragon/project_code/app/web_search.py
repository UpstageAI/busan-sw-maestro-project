"""웹검색 클라이언트 — RAG 커버리지 부족 시 근거를 보강한다.

기본 제공자는 **마인크래프트 위키(ko.minecraft.wiki)의 공개 MediaWiki API**라서
키가 필요 없다(라이브 위키 전체 검색 → RAG가 놓친 문서 보강). Tavily는 키가 있을 때
일반 웹까지 넓히는 선택적 폴백이다.

검색 결과는 Qdrant 검색(search_documents)과 동일한 형태로 변환해, 코치 응답이
위키 문서와 똑같이 다룰 수 있게 한다. 호출이 실패하면 빈 목록을 반환해(best-effort)
기존 흐름을 깨지 않는다.
"""
import logging
from urllib.parse import quote

import httpx

from app.core.config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

_WIKI_API = "https://ko.minecraft.wiki/api.php"
_USER_AGENT = "EnderDragonCoach/0.1 (Minecraft beginner coaching bot)"
_TAVILY_URL = "https://api.tavily.com/search"


def wiki_search(query: str, max_results: int = 3) -> list[dict]:
    """마크 위키(ko.minecraft.wiki)를 키 없이 검색해 search_results 형식으로 반환한다.

    generator=search로 관련 문서를 찾고 prop=extracts로 도입부 본문을 한 번에 가져온다.
    실패하면 빈 목록(best-effort). 반환 각 항목의 distance는 1.0(직접 위키 검색이라 신뢰).
    """
    try:
        resp = httpx.get(
            _WIKI_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": max_results,
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "format": "json",
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("위키 검색 실패(무시): %s", e)
        return []

    pages = (data.get("query") or {}).get("pages") or {}
    # generator=search 결과는 index로 관련도 순서를 준다.
    ordered = sorted(pages.values(), key=lambda p: p.get("index", 999))
    results = []
    for p in ordered:
        extract = (p.get("extract") or "").strip()
        if not extract:
            continue
        title = p.get("title", "")
        results.append({
            "content": extract[:1500],
            "metadata": {"title": f"{title} (위키)", "url": f"https://ko.minecraft.wiki/w/{quote(title)}"},
            "distance": 1.0,
            "source": "wiki",
        })
        if len(results) >= max_results:
            break
    return results


def tavily_search(query: str, max_results: int = 3) -> list[dict]:
    """Tavily 웹검색 결과를 search_results 형식으로 반환한다(키 없거나 실패면 []).

    반환: [{"content", "metadata": {"title", "url"}, "distance", "source": "web"}, ...]
    distance에는 Tavily 관련도 점수를 담아 위키 결과와 동일하게 다룬다.
    """
    if not TAVILY_API_KEY:
        return []
    try:
        resp = httpx.post(
            _TAVILY_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Tavily 검색 실패(무시): %s", e)
        return []

    results = []
    for r in data.get("results", []):
        title = (r.get("title") or "").strip()
        results.append({
            "content": r.get("content", ""),
            "metadata": {"title": f"{title} (웹)" if title else "웹 검색", "url": r.get("url", "")},
            "distance": r.get("score", 0.0),
            "source": "web",
        })
    return results

"""web_search 노드(폴백) 테스트.

네트워크 없이 결정론으로 검증한다: 커버리지 게이트, 키 없이 위키 보강,
위키가 비면 Tavily 폴백, 병합. wiki_search·tavily_search는 가짜로 교체한다.
"""
from app.agents import web_searcher


def test_needs_web_빈결과나_낮은유사도면_True():
    assert web_searcher._needs_web([], 0.5) is True
    assert web_searcher._needs_web([{"distance": 0.2}], 0.5) is True


def test_needs_web_충분한_유사도면_False():
    assert web_searcher._needs_web([{"distance": 0.9}, {"distance": 0.3}], 0.5) is False


def test_커버리지_충분하면_검색_스킵(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(web_searcher, "wiki_search", lambda *a, **k: called.__setitem__("n", called["n"] + 1) or [])
    monkeypatch.setattr(web_searcher, "tavily_search", lambda *a, **k: called.__setitem__("n", called["n"] + 1) or [])
    out = web_searcher.search_web({"query": "철 곡괭이", "search_results": [{"distance": 0.9}]})
    assert out == {}
    assert called["n"] == 0  # 충분하므로 호출조차 안 함


def test_키_없어도_위키로_보강한다(monkeypatch):
    # TAVILY 키가 없어도 키리스 위키 검색으로 보강돼야 한다.
    monkeypatch.setattr(web_searcher, "TAVILY_API_KEY", "")
    wiki_doc = {"content": "위키 내용", "metadata": {"title": "화로 (위키)"}, "distance": 1.0, "source": "wiki"}
    monkeypatch.setattr(web_searcher, "wiki_search", lambda *a, **k: [wiki_doc])
    out = web_searcher.search_web({"query": "화로 만드는 법", "search_results": []})
    assert out["search_results"] == [wiki_doc]


def test_위키_우선_병합하고_타비리는_부르지_않는다(monkeypatch):
    wiki_doc = {"content": "위키", "metadata": {"title": "철 곡괭이 (위키)"}, "distance": 1.0, "source": "wiki"}
    tavily_called = {"n": 0}
    monkeypatch.setattr(web_searcher, "wiki_search", lambda *a, **k: [wiki_doc])
    monkeypatch.setattr(web_searcher, "TAVILY_API_KEY", "fake-key")
    monkeypatch.setattr(web_searcher, "tavily_search", lambda *a, **k: tavily_called.__setitem__("n", 1) or [])
    existing = [{"content": "약한 위키", "metadata": {"title": "위키"}, "distance": 0.1}]
    out = web_searcher.search_web({
        "query": "잘 안 나오는 질문",
        "query_analysis": {"keywords": ["철", "곡괭이"]},
        "search_results": existing,
    })
    assert out["search_results"] == existing + [wiki_doc]
    assert tavily_called["n"] == 0  # 위키가 결과를 주면 Tavily는 호출 안 함


def test_위키_비면_키_있을때_타비리로_폴백(monkeypatch):
    web_doc = {"content": "웹", "metadata": {"title": "X (웹)"}, "distance": 0.8, "source": "web"}
    monkeypatch.setattr(web_searcher, "wiki_search", lambda *a, **k: [])
    monkeypatch.setattr(web_searcher, "TAVILY_API_KEY", "fake-key")
    monkeypatch.setattr(web_searcher, "tavily_search", lambda *a, **k: [web_doc])
    out = web_searcher.search_web({"query": "q", "search_results": []})
    assert out["search_results"] == [web_doc]


def test_둘다_비면_빈_업데이트(monkeypatch):
    monkeypatch.setattr(web_searcher, "wiki_search", lambda *a, **k: [])
    monkeypatch.setattr(web_searcher, "TAVILY_API_KEY", "")
    out = web_searcher.search_web({"query": "q", "search_results": []})
    assert out == {}

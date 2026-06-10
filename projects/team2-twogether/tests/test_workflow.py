"""워크플로우 그래프(Phase 2 · 1단계) end-to-end 테스트.

`build_graph()` 로 컴파일한 LangGraph 를 단일 진입점으로 invoke 하여, 프론트 계약
(`final_response`)이 status 3종으로 올바르게 산출되는지 검증한다. 검색 모드는 기본
`bm25` 로 외부 API(Upstage/Qdrant) 미호출 — 순수 로컬.

도달성 참고:
- need_clarification / recommended 는 자연 입력으로 도달 가능 → E2E 로 검증.
- limited / retry 루프는 현재 규칙 기반 모드에서 자연 입력으로는 도달 불가하다.
  fit_evaluation 이 max-정규화로 최고점을 항상 100 으로 만들어 후보가 하나라도 있으면
  is_recommendation_confident 가 참이 되고, BM25 는 항상 후보를 반환하기 때문.
  → 분기 배선은 (1) 라우터 함수 단위 테스트와 (2) 멘토 DB 가 빈 경우의 E2E 루프
     테스트로 결정적으로 커버한다. (LLM swap-in 후에는 자연 도달하게 됨)
"""

from backend.app.graph.workflow import (
    MAX_RETRY,
    _route_after_fit,
    _route_after_parse,
    build_graph,
)
from backend.app.schemas.response import (
    ClarificationResponse,
    LimitedResponse,
    RecommendedResponse,
)


# --- E2E: 도달 가능한 경로 -------------------------------------------------

def test_clarification_path_short_circuits_pipeline():
    """입력 부족 → need_clarification, 노드2~4 미실행(검색 결과 없음)."""
    graph = build_graph()
    result = graph.invoke({"user_input": "앱 만들어요"})

    final = result["final_response"]
    assert final["status"] == "need_clarification"
    assert final["question"]  # 질문 비어있지 않음
    assert isinstance(final["options"], list)
    # 스키마 정합 검증
    ClarificationResponse(**final)
    # 본 파이프라인은 돌지 않았다
    assert not result.get("retrieved_mentors")


def test_recommended_path_produces_cards():
    """충분한 입력 → recommended, 카드 산출, 깨끗한 keywords 보존."""
    graph = build_graph()
    result = graph.invoke({
        "user_input": "FastAPI로 추천 API를 만드는데 모델 서빙 구조와 Docker 배포가 어렵습니다",
        "tech_stack": ["Python", "FastAPI"],
    })

    final = result["final_response"]
    assert final["status"] == "recommended"
    assert final["mentors"]  # 최소 1명
    assert final["refined"] is False  # 첫 패스에서 신뢰 → 재검색 없음
    # 스키마 정합 검증 (status discriminated union)
    RecommendedResponse(**final)
    # 카드에 내부 필드가 새지 않는다
    card = final["mentors"][0]
    assert "mentor_id" not in card
    assert "retrieval_score" not in card
    assert card["keywords"]  # 키워드 보존


# --- E2E: 멘토 DB 가 비면 limited + retry 루프 (결정적) ---------------------

def test_limited_and_retry_when_no_mentors(monkeypatch):
    """멘토 DB 가 비면: 저신뢰 → query_refiner 재검색 1회 → 소진 → limited.

    retry 루프와 limited shaping, 루프 종료(무한루프 아님)를 end-to-end 로 검증한다.
    멘토 0명 = '추천할 멘토 없음' 이라는 정당한 경계 조건을 사용.
    """
    import backend.app.nodes.mentor_retrieval as mr
    import backend.app.nodes.result_builder as rb

    monkeypatch.setattr(mr, "load_mentors", lambda *a, **k: [])
    monkeypatch.setattr(rb, "load_mentors", lambda *a, **k: [])

    graph = build_graph()
    result = graph.invoke({
        "user_input": "FastAPI로 추천 API를 만드는데 모델 서빙 구조와 Docker 배포가 어렵습니다",
        "tech_stack": ["Python", "FastAPI"],
    })

    final = result["final_response"]
    assert final["status"] == "limited"
    assert final["notice"]  # 안내 문구 존재
    LimitedResponse(**final)
    # 재검색이 정확히 MAX_RETRY 회 일어나고 종료됐다
    assert result.get("retry_count") == MAX_RETRY


# --- 단위: 분기 라우터 ------------------------------------------------------

def test_route_after_parse_branches():
    assert _route_after_parse({"is_input_sufficient": True}) == "interview_gap"
    assert _route_after_parse({"is_input_sufficient": False}) == "clarification"
    assert _route_after_parse({}) == "clarification"  # 기본 안전값


def test_route_after_fit_confident_goes_to_builder():
    assert _route_after_fit({"is_recommendation_confident": True}) == "result_builder"


def test_route_after_fit_low_confidence_retries_then_exhausts():
    # 저신뢰 & 재시도 여유 → query_refiner
    assert _route_after_fit(
        {"is_recommendation_confident": False, "retry_count": 0}
    ) == "query_refiner"
    # 저신뢰 & 재시도 소진 → result_builder (limited)
    assert _route_after_fit(
        {"is_recommendation_confident": False, "retry_count": MAX_RETRY}
    ) == "result_builder"

"""result_builder(워크플로우 4) 단위 테스트.

순수 함수 build_recommendation_response 와 노드 래퍼 result_builder_node 를
프론트 계약(frontend/src/types/api.ts) 기준으로 검증한다.
"""

from backend.app.nodes.result_builder import (
    TOP_N,
    build_recommendation_response,
    result_builder_node,
)
from backend.app.schemas.response import (
    LimitedResponse,
    RecommendedResponse,
)


def _evaluated(name, score, mentor_id="", **extra):
    base = {
        "name": name,
        "domain": ["MLOps", "Infra"],
        "score": score,
        "reason": f"{name} 근거",
        "matched_keywords": ["model serving", "docker"],
        "mentor_id": mentor_id,
        "can_help": ["모델 서빙 구조 설계"],
        "less_relevant_for": ["브랜딩 전략"],
        "profile_summary": f"{name} 요약",
        "retrieval_score": 10.0,
    }
    base.update(extra)
    return base


def _gap():
    return {
        "main_gap": "모델 서빙 역량",
        "gap_categories": ["MLOps", "배포"],
        "needed_mentor_expertise": ["model serving"],
    }


# ── recommended ──────────────────────────────────────────────────────────
def test_recommended_basic():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 92.0), _evaluated("장민서", 85.0)],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    res = build_recommendation_response(state)

    assert res["status"] == "recommended"
    assert res["gaps"] == ["MLOps", "배포"]
    assert res["refined"] is False
    assert [m["name"] for m in res["mentors"]] == ["서지훈", "장민서"]
    # pydantic 검증 통과(계약 일치)
    RecommendedResponse(**res)


def test_card_drops_internal_fields_and_maps_shape():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 92.4)],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    card = build_recommendation_response(state)["mentors"][0]

    # 내부 전용 필드는 카드에서 제거
    for internal in ("mentor_id", "retrieval_score", "matched_keywords"):
        assert internal not in card
    # 프론트 Mentor 필드 모두 존재
    assert set(card) == {
        "name", "domain", "keywords", "score",
        "reason", "can_help", "less_relevant_for", "profile_summary",
    }
    # 점수는 정수로 반올림
    assert card["score"] == 92
    assert isinstance(card["score"], int)


def test_reason_passthrough_no_fabrication():
    """환각 방지: reason 은 입력 그대로 노출(변형 금지)."""
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 90.0, reason="정확히 이 문장")],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    card = build_recommendation_response(state)["mentors"][0]
    assert card["reason"] == "정확히 이 문장"


def test_top_n_limit():
    mentors = [_evaluated(f"멘토{i}", 90 - i) for i in range(6)]
    state = {
        "evaluated_mentors": mentors,
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    res = build_recommendation_response(state)
    assert len(res["mentors"]) == TOP_N


def test_refined_flag_from_retry_count():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 90.0)],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 1,
    }
    assert build_recommendation_response(state)["refined"] is True


# ── limited ──────────────────────────────────────────────────────────────
def test_limited_when_not_confident():
    state = {
        "evaluated_mentors": [_evaluated("오현우", 55.0), _evaluated("김나래", 50.0)],
        "gap_context": _gap(),
        "is_recommendation_confident": False,
        "retry_count": 1,
    }
    res = build_recommendation_response(state)

    assert res["status"] == "limited"
    assert "notice" in res and res["notice"]
    assert len(res["mentors"]) == 2
    LimitedResponse(**res)


def test_limited_notice_splices_only_real_gap():
    """notice 는 gap_context 의 실제 값만 끼워 넣는다(환각 방지)."""
    state = {
        "evaluated_mentors": [_evaluated("오현우", 55.0)],
        "gap_context": {"main_gap": "실시간 영상 처리", "gap_categories": ["Realtime"]},
        "is_recommendation_confident": False,
        "retry_count": 1,
    }
    notice = build_recommendation_response(state)["notice"]
    assert "실시간 영상 처리" in notice


# ── empty ────────────────────────────────────────────────────────────────
def test_empty_mentors_is_limited_with_guidance():
    state = {
        "evaluated_mentors": [],
        "gap_context": _gap(),
        "is_recommendation_confident": False,
        "retry_count": 1,
    }
    res = build_recommendation_response(state)
    assert res["status"] == "limited"
    assert res["mentors"] == []
    assert res["notice"]  # 빈 결과 안내 문구 존재
    LimitedResponse(**res)


def test_confident_but_no_mentors_falls_back_to_limited():
    """방어: confident=True 라도 멘토 0건이면 recommended 로 내보내지 않는다."""
    state = {
        "evaluated_mentors": [],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    assert build_recommendation_response(state)["status"] == "limited"


# ── gaps fallback ────────────────────────────────────────────────────────
def test_gaps_fallback_to_main_gap():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 90.0)],
        "gap_context": {"main_gap": "배포 역량", "gap_categories": []},
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    assert build_recommendation_response(state)["gaps"] == ["배포 역량"]


def test_missing_gap_context_is_safe():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 90.0)],
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    res = build_recommendation_response(state)
    assert res["gaps"] == []
    assert res["status"] == "recommended"


# ── 노드 래퍼 ────────────────────────────────────────────────────────────
def test_node_wrapper_state_keys():
    state = {
        "evaluated_mentors": [_evaluated("서지훈", 90.0)],
        "gap_context": _gap(),
        "is_recommendation_confident": True,
        "retry_count": 0,
    }
    update = result_builder_node(state)
    assert "final_response" in update
    assert update["final_response"]["status"] == "recommended"
    assert update["final_recommendations"] == update["final_response"]["mentors"]
    assert update["message"] == ""  # recommended 엔 notice 없음

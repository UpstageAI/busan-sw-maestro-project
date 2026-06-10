"""API 서버(Phase 2 · 2단계) 테스트 — FastAPI TestClient.

``POST /recommend`` 가 그래프를 invoke 해 프론트 계약(status 3종)을 반환하는지,
그리고 인메모리 세션이 확인 질문 왕복에서 원본 입력을 기억하는지 검증한다.
검색은 기본 bm25 — 외부 API 미호출.
"""

from fastapi.testclient import TestClient

from backend.app.main import _SESSIONS, app
from backend.app.schemas.response import (
    ClarificationResponse,
    RecommendedResponse,
)

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_recommend_clarification():
    """입력 부족 → need_clarification."""
    res = client.post("/recommend", json={
        "session_id": "s-clar",
        "project_text": "앱 만들어요",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "need_clarification"
    assert body["question"]
    ClarificationResponse(**body)


def test_recommend_recommended():
    """충분한 입력 → recommended, 카드 산출."""
    res = client.post("/recommend", json={
        "session_id": "s-rec",
        "project_text": "FastAPI로 추천 API를 만드는데 모델 서빙 구조와 Docker 배포가 어렵습니다",
        "tech_stack": ["Python", "FastAPI"],
    })
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "recommended"
    assert body["mentors"]
    RecommendedResponse(**body)


def test_session_remembers_original_input_across_clarification():
    """확인 질문 왕복: 후속 요청이 clarify_answer 만 보내도 원본 입력과 병합된다."""
    sid = "s-flow"
    # 1) 입력 부족 → 확인 질문. 세션에 원본 보관됨.
    first = client.post("/recommend", json={
        "session_id": sid,
        "project_text": "추천 서비스 만들어요",
    }).json()
    assert first["status"] == "need_clarification"
    assert sid in _SESSIONS  # 세션 유지 중

    # 2) project_text 재전송 없이 clarify_answer 만 전송 → 원본과 병합되어 진행.
    second = client.post("/recommend", json={
        "session_id": sid,
        "project_text": "",  # 프론트가 원본을 안 보내는 경우
        "clarify_answer": "Python FastAPI로 모델 서빙과 Docker 배포가 어렵습니다",
    }).json()
    assert second["status"] in ("recommended", "limited")
    # 대화 종료 → 세션 정리됨.
    assert sid not in _SESSIONS


def test_session_isolated_per_id():
    """서로 다른 session_id 는 독립적으로 처리된다."""
    a = client.post("/recommend", json={
        "session_id": "iso-a", "project_text": "앱이요",
    }).json()
    b = client.post("/recommend", json={
        "session_id": "iso-b",
        "project_text": "FastAPI로 추천 API를 만드는데 모델 서빙과 Docker 배포가 어렵습니다",
        "tech_stack": ["Python"],
    }).json()
    assert a["status"] == "need_clarification"
    assert b["status"] == "recommended"

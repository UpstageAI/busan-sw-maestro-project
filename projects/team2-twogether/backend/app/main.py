"""멘토 추천 API 서버 — FastAPI (Phase 2 · 2단계).

워크플로우 그래프(`backend/app/graph/workflow.py`)를 단일 엔드포인트
``POST /recommend`` 로 노출한다. 요청을 그래프 state 로 변환해 invoke 하고,
그래프가 산출한 프론트 계약(`final_response`)을 그대로 반환한다.

세션: 인메모리(`_SESSIONS`). 확인 질문(need_clarification) 왕복 동안 원본 입력
(project_text/tech_stack/stage)을 session_id 별로 기억해, 후속 요청이 clarify_answer
만 보내도 원본과 병합되도록 한다. 대화가 끝나면(추천/제한 응답) 세션을 비운다.
프로세스 재시작 시 휘발 — 데모/단일 인스턴스 전제.

LLM 미사용, 검색은 기본 bm25(외부 API 미호출).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.graph.workflow import build_graph
from backend.app.schemas.request import RecommendRequest

#: 프론트 dev 서버 origin (Vite 기본 5173, CRA 3000). 데모용으로 넓게 허용.
_ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

#: session_id → 원본 입력(user_input/tech_stack/stage). 인메모리, 휘발성.
_SESSIONS: dict[str, dict[str, Any]] = {}

app = FastAPI(title="멘토 추천 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

#: 컴파일된 그래프는 1회만 생성해 재사용(노드/엣지는 상태 없음).
_GRAPH = build_graph()


def _build_graph_input(req: RecommendRequest) -> dict[str, Any]:
    """요청 → 그래프 진입 state. 세션이 있으면 원본 입력과 병합한다."""
    base = {
        "user_input": req.project_text,
        "tech_stack": req.tech_stack,
        "stage": req.stage,
    }

    # 확인 질문 후속: 저장된 원본 입력을 우선 사용(프론트가 원본을 재전송하지
    # 않아도 동작). clarify_answer 는 parse_input 이 원본과 병합한다.
    if req.clarify_answer and req.session_id in _SESSIONS:
        base = {**_SESSIONS[req.session_id], **{
            k: v for k, v in base.items() if v
        }}

    state = {**base, "clarify_answer": req.clarify_answer}

    # 신규 요청은 원본 입력을 세션에 보관(후속 확인 질문 왕복 대비).
    if req.session_id and not req.clarify_answer:
        _SESSIONS[req.session_id] = base

    return state


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend")
def recommend(req: RecommendRequest) -> dict[str, Any]:
    """추천 요청 → 그래프 invoke → 프론트 계약(final_response) 반환."""
    graph_input = _build_graph_input(req)
    result = _GRAPH.invoke(graph_input)
    final_response: dict[str, Any] = result["final_response"]

    # 대화 종료(추천/제한)면 세션 정리. 확인 질문이면 유지.
    if req.session_id and final_response.get("status") != "need_clarification":
        _SESSIONS.pop(req.session_id, None)

    return final_response

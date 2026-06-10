"""멘토 추천 워크플로우 — LangGraph 그래프 조립 (Phase 2 · 1단계).

노드 1~4(개별 함수로 완성)를 하나의 StateGraph 로 배선한다. 단일 진입점에서
입력을 받아 프론트 계약(`final_response`)을 산출하는 컴파일된 그래프를 만든다.

흐름::

    START → input_parser ─┬─ (입력 부족) → clarification → END
                          └─ (충분)      → interview_gap → mentor_retrieval
                                            → fit_evaluation ─┬─ (신뢰)        → result_builder → END
                                                              ├─ (저신뢰·재시도) → query_refiner → mentor_retrieval
                                                              └─ (저신뢰·소진)   → result_builder → END

설계 노트:
- 노드 함수(타 작업자 소유)는 무수정. 명명 불일치(`parse_input` vs `*_node`)는
  그래프 노드명으로 흡수한다.
- 그래프가 status 3종 모두에 대해 `final_response` 를 산출하므로(클래리피케이션
  포함), API 서버는 invoke 후 `final_response` 만 반환하면 된다.
- LLM 미사용(노드들은 규칙 기반 경로로 완주), 세션은 서버단(인메모리) 책임.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.app.graph.state import GraphState
from backend.app.nodes.fit_evaluation import fit_evaluation_node
from backend.app.nodes.input_parser import parse_input
from backend.app.nodes.interview_gap import interview_gap_node
from backend.app.nodes.mentor_retrieval import mentor_retrieval_node
from backend.app.nodes.query_refiner import query_refiner_node
from backend.app.nodes.result_builder import result_builder_node

#: 저신뢰 추천 시 query_refiner 재검색 최대 횟수.
MAX_RETRY = 1


def clarification_node(state: dict[str, Any]) -> dict[str, Any]:
    """입력 부족 → 확인 질문 응답(need_clarification) 페이로드 생성.

    ``parse_input`` 이 state 에 넣어둔 clarification 필드를 프론트 계약
    (`ClarificationResponse`)으로 변환한다. result_builder 가 recommended/limited
    를 shaping 하는 것과 대칭으로, 그래프가 항상 ``final_response`` 를 산출하게 한다.
    """
    return {
        "final_response": {
            "status": "need_clarification",
            "question": state.get("clarification_question", ""),
            "options": state.get("clarification_options", []),
        }
    }


def _route_after_parse(state: dict[str, Any]) -> str:
    """노드1 이후 분기: 입력이 충분하면 본 파이프라인, 아니면 확인 질문."""
    if state.get("is_input_sufficient"):
        return "interview_gap"
    return "clarification"


def _route_after_fit(state: dict[str, Any]) -> str:
    """노드3 이후 분기: 신뢰/재검색/소진.

    - 신뢰(confident) → 결과 빌더
    - 저신뢰 & 재시도 여유(retry_count < MAX_RETRY) → 쿼리 보강 후 재검색
    - 저신뢰 & 재시도 소진 → 결과 빌더(limited 로 산출)
    """
    if state.get("is_recommendation_confident"):
        return "result_builder"
    if int(state.get("retry_count", 0) or 0) < MAX_RETRY:
        return "query_refiner"
    return "result_builder"


def build_graph():
    """노드 1~4 를 배선한 컴파일된 LangGraph 그래프를 반환한다."""
    graph = StateGraph(GraphState)

    graph.add_node("input_parser", parse_input)
    graph.add_node("clarification", clarification_node)
    graph.add_node("interview_gap", interview_gap_node)
    graph.add_node("mentor_retrieval", mentor_retrieval_node)
    graph.add_node("fit_evaluation", fit_evaluation_node)
    graph.add_node("query_refiner", query_refiner_node)
    graph.add_node("result_builder", result_builder_node)

    graph.add_edge(START, "input_parser")
    graph.add_conditional_edges(
        "input_parser",
        _route_after_parse,
        {"interview_gap": "interview_gap", "clarification": "clarification"},
    )
    graph.add_edge("clarification", END)

    graph.add_edge("interview_gap", "mentor_retrieval")
    graph.add_edge("mentor_retrieval", "fit_evaluation")
    graph.add_conditional_edges(
        "fit_evaluation",
        _route_after_fit,
        {"query_refiner": "query_refiner", "result_builder": "result_builder"},
    )
    graph.add_edge("query_refiner", "mentor_retrieval")
    graph.add_edge("result_builder", END)

    return graph.compile()

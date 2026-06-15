"""단일 LangGraph 조립 (6-1 Item 입력 -> 6-2 -> 6-3).

동기식 사용자 개입은 LangGraph `interrupt()`로 그래프 중간에서 정지하고,
checkpointer(MemorySaver) + thread_id 로 상태를 보관했다가 resume 으로 재개한다.
HITL 은 2단계다: 1차 승인(request_approval), 2차 선호 확인(preference_interrupt).

흐름:
  START -> analysis(pass-through) -> tool_selection -> conflict_check
        -> [reviewables 있으면] request_approval(1차 interrupt) -> execution
        -> feedback_entry(6-3 seam) -> feedback_analyze
        -> [후보 있으면] preference_interrupt(2차 interrupt) -> preference_store -> END
        -> [후보 없으면] END
        ([reviewables 없으면] conflict_check -> feedback_entry 로 바로)
"""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.analysis import analysis_node
from app.agent.nodes.approval import request_approval_node
from app.agent.nodes.conflict_check import conflict_check_node
from app.agent.nodes.execution import execution_node
from app.agent.nodes.feedback_analyze import feedback_analyze_node
from app.agent.nodes.feedback_seam import feedback_entry_node
from app.agent.nodes.preference import (
    preference_interrupt_node,
    preference_store_node,
)
from app.agent.nodes.tool_selection import tool_selection_node
from app.agent.state import AgentState


def _route_after_conflict(state: dict) -> str:
    # 검토할 항목이 없으면(전부 ignore/skipped) 승인 단계를 건너뛴다.
    return "request_approval" if state.get("reviewables") else "feedback_entry"


def _route_after_feedback(state: dict) -> str:
    # 선호 후보가 없으면(수정 없음) 2차 interrupt 를 건너뛰고 종료한다.
    return "preference_interrupt" if state.get("candidates") else END


@lru_cache(maxsize=1)
def build_graph():
    """단일 그래프를 컴파일한다 (MemorySaver 포함, 프로세스 내 1회).

    lru_cache 로 동일 인스턴스를 재사용하므로 /run 과 /resume 이 같은 checkpointer
    상태를 thread_id 로 공유한다.

    제약(단일 워커 전제): MemorySaver 는 프로세스 인메모리이고 lru_cache 도 프로세스
    스코프다. 따라서 uvicorn 다중 워커(--workers N)나 dev 리로드 환경에서는 /run 과
    /resume 이 서로 다른 프로세스에 분배되면 resume 이 thread 상태를 찾지 못한다.
    서버 재시작 시 진행 중 세션도 소실된다. 운영 전환 시 SqliteSaver/PostgresSaver 로
    교체한다.
    """
    g = StateGraph(AgentState)
    g.add_node("analysis", analysis_node)
    g.add_node("tool_selection", tool_selection_node)
    g.add_node("conflict_check", conflict_check_node)
    g.add_node("request_approval", request_approval_node)
    g.add_node("execution", execution_node)
    g.add_node("feedback_entry", feedback_entry_node)
    g.add_node("feedback_analyze", feedback_analyze_node)
    g.add_node("preference_interrupt", preference_interrupt_node)
    g.add_node("preference_store", preference_store_node)

    g.add_edge(START, "analysis")
    g.add_edge("analysis", "tool_selection")
    g.add_edge("tool_selection", "conflict_check")
    g.add_conditional_edges(
        "conflict_check",
        _route_after_conflict,
        {"request_approval": "request_approval", "feedback_entry": "feedback_entry"},
    )
    g.add_edge("request_approval", "execution")
    g.add_edge("execution", "feedback_entry")
    g.add_edge("feedback_entry", "feedback_analyze")
    g.add_conditional_edges(
        "feedback_analyze",
        _route_after_feedback,
        {"preference_interrupt": "preference_interrupt", END: END},
    )
    g.add_edge("preference_interrupt", "preference_store")
    g.add_edge("preference_store", END)

    return g.compile(checkpointer=MemorySaver())

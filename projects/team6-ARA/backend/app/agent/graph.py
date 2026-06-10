"""단일 LangGraph 조립 (6-1 Item 입력 -> 6-2 -> 6-3 seam).

동기식 사용자 승인은 LangGraph `interrupt()`로 그래프 중간에서 정지하고,
checkpointer(MemorySaver) + thread_id 로 상태를 보관했다가 resume 으로 재개한다.

흐름:
  START -> analysis(pass-through) -> tool_selection -> conflict_check
        -> [reviewables 있으면] request_approval(interrupt) -> execution
        -> feedback_entry(6-3 seam) -> END
        ([reviewables 없으면] conflict_check -> feedback_entry 로 바로)

6-3(피드백/선호)은 feedback_entry 다음에 노드를 붙여 흡수한다(현재는 END).
"""

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.analysis import analysis_node
from app.agent.nodes.approval import request_approval_node
from app.agent.nodes.conflict_check import conflict_check_node
from app.agent.nodes.execution import execution_node
from app.agent.nodes.feedback_seam import feedback_entry_node
from app.agent.nodes.tool_selection import tool_selection_node
from app.agent.state import AgentState


def _route_after_conflict(state: dict) -> str:
    # 검토할 항목이 없으면(전부 ignore/skipped) 승인 단계를 건너뛴다.
    return "request_approval" if state.get("reviewables") else "feedback_entry"


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
    g.add_edge("feedback_entry", END)

    return g.compile(checkpointer=MemorySaver())

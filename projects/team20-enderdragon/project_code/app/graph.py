# ========================================
# Minecraft Guide Agent - LangGraph workflow
# load_state -> analyze -> resolve_goal -> clarify -> retrieve -> web_search -> check_materials -> reconcile -> respond -> persist_state
# load_state      : 직전 턴 진척도(목표·인벤토리) 로드
# resolve_goal    : 목표 클래스 분류 + 막연한 질문이면 상태 근거로 다음 목표 제안
# clarify         : 정보 부족 시 되묻기, 충분하면 통과
# web_search      : 위키 커버리지 부족 시에만 웹검색으로 근거 보강(키 없으면 스킵)
# check_materials : 제작 목표가 있으면 결정론으로 부족 자원·채굴 티어 계산
# reconcile       : 직전 인벤토리와 비교해 새로 얻은 재료(진행) 인식
# persist_state   : 이번 턴 진척도 저장 (모든 종료 경로 공통)
# ========================================
from langgraph.graph import StateGraph, START, END
from app.schemas import AgentState
from app.agents.query_analyzer import analyze_query
from app.agents.goal_resolver import resolve_goal
from app.agents.retrieval import retrieve_context
from app.agents.responder import generate_answer
from app.agents.clarifier import check_and_clarify
from app.agents.web_searcher import search_web
from app.agents.material_checker import check_materials
from app.agents.session_memory import load_state, reconcile, persist_state

def route_by_domain(state: AgentState) -> str:
    """analyze 후 도메인 분기: 마인크래프트면 resolve_goal(목표 해석)로, 그 외엔 곧장 respond로."""
    return "resolve_goal" if state.get("domain", "minecraft") == "minecraft" else "respond"


def route_by_clarification(state: AgentState) -> str:
    return "ask" if state.get("need_clarification") else "retrieve"


def ask_clarification(state: AgentState) -> dict:
    question = state.get("clarification_question", "Could you tell me more?")
    return {"final_answer": question}


def create_graph():
    builder = StateGraph(AgentState)
    builder.add_node("load_state", load_state)
    builder.add_node("analyze", analyze_query)
    builder.add_node("resolve_goal", resolve_goal)
    builder.add_node("clarify", check_and_clarify)
    builder.add_node("ask", ask_clarification)
    builder.add_node("retrieve", retrieve_context)
    builder.add_node("web_search", search_web)
    builder.add_node("check_materials", check_materials)
    builder.add_node("reconcile", reconcile)
    builder.add_node("respond", generate_answer)
    builder.add_node("persist_state", persist_state)
    builder.add_edge(START, "load_state")
    builder.add_edge("load_state", "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_by_domain,
        {"resolve_goal": "resolve_goal", "respond": "respond"},
    )
    builder.add_edge("resolve_goal", "clarify")
    builder.add_conditional_edges(
        "clarify",
        route_by_clarification,
        {"ask": "ask", "retrieve": "retrieve"},
    )
    builder.add_edge("retrieve", "web_search")
    builder.add_edge("web_search", "check_materials")
    builder.add_edge("check_materials", "reconcile")
    builder.add_edge("reconcile", "respond")
    # 모든 종료 경로는 persist_state를 거쳐 진척도를 저장한다.
    builder.add_edge("ask", "persist_state")
    builder.add_edge("respond", "persist_state")
    builder.add_edge("persist_state", END)
    return builder.compile()

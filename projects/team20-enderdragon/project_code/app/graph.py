# ========================================
# Minecraft Guide Agent - LangGraph workflow
# analyze -> clarify -> retrieve -> respond (5 nodes)
# clarify: ask follow-up if info insufficient, pass through if sufficient
# ========================================
from langgraph.graph import StateGraph, START, END
from app.schemas import AgentState
from app.agents.query_analyzer import analyze_query
from app.agents.retrieval import retrieve_context
from app.agents.responder import generate_answer
from app.agents.clarifier import check_and_clarify

def route_by_domain(state: AgentState) -> str:
    """analyze 후 도메인 분기: 마인크래프트면 clarify(되묻기 판단)로, 그 외엔 곧장 respond로."""
    return "clarify" if state.get("domain", "minecraft") == "minecraft" else "respond"


def route_by_clarification(state: AgentState) -> str:
    return "ask" if state.get("need_clarification") else "retrieve"


def ask_clarification(state: AgentState) -> dict:
    question = state.get("clarification_question", "Could you tell me more?")
    return {"final_answer": question}


def create_graph():
    builder = StateGraph(AgentState)
    builder.add_node("analyze", analyze_query)
    builder.add_node("clarify", check_and_clarify)
    builder.add_node("ask", ask_clarification)
    builder.add_node("retrieve", retrieve_context)
    builder.add_node("respond", generate_answer)
    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_by_domain,
        {"clarify": "clarify", "respond": "respond"},
    )
    builder.add_conditional_edges(
        "clarify",
        route_by_clarification,
        {"ask": "ask", "retrieve": "retrieve"},
    )
    builder.add_edge("ask", END)
    builder.add_edge("retrieve", "respond")
    builder.add_edge("respond", END)
    return builder.compile()

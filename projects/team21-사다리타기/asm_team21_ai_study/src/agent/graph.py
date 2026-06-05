from __future__ import annotations

import logging
import time
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes.format_schedule import format_schedule_node
from .nodes.generate_answer import generate_answer_node
from .nodes.generate_summary import generate_summary_node
from .nodes.handle_general import handle_general_node
from .nodes.handle_irrelevant import handle_irrelevant_node
from .nodes.handle_not_found import handle_not_found_node
from .nodes.retrieve import retrieve_node
from .nodes.router import router_node
from .state import AgentState

logger = logging.getLogger(__name__)


def _logged(name: str, fn):
    def wrapper(state: AgentState):
        logger.info("[GRAPH] ▶ %s", name)
        t0 = time.perf_counter()
        result = fn(state)
        logger.info("[GRAPH] ✓ %s (%.2fs)", name, time.perf_counter() - t0)
        return result
    wrapper.__name__ = name
    return wrapper


# ── 조건부 엣지 함수 ─────────────────────────────────────────────────

def _route_after_router(state: AgentState) -> str:
    intent = state["intent"]
    if intent == "general":
        next_node = "handle_general"
    elif intent == "soma_unrelated":
        next_node = "handle_irrelevant"
    else:
        next_node = "retrieve_documents"
    logger.info("[GRAPH] ⤷ router → %s (intent=%s)", next_node, intent)
    return next_node


def _route_after_retrieve(state: AgentState) -> str:
    if not state["retrieved_chunks"]:
        next_node = "handle_not_found"
    else:
        intent = state["intent"]
        mapping = {
            "soma_query":     "generate_answer",
            "soma_summarize": "generate_summary",
            "schedule_link":  "format_schedule_link",
        }
        next_node = mapping.get(intent, "generate_answer")
    logger.info("[GRAPH] ⤷ retrieve_documents → %s", next_node)
    return next_node


# ── 그래프 조립 ──────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("router",               _logged("router",               router_node))
    g.add_node("handle_general",       _logged("handle_general",       handle_general_node))
    g.add_node("handle_irrelevant",    _logged("handle_irrelevant",    handle_irrelevant_node))
    g.add_node("retrieve_documents",   _logged("retrieve_documents",   retrieve_node))
    g.add_node("generate_answer",      _logged("generate_answer",      generate_answer_node))
    g.add_node("generate_summary",     _logged("generate_summary",     generate_summary_node))
    g.add_node("format_schedule_link", _logged("format_schedule_link", format_schedule_node))
    g.add_node("handle_not_found",     _logged("handle_not_found",     handle_not_found_node))

    g.add_edge(START, "router")

    g.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "handle_general":    "handle_general",
            "handle_irrelevant": "handle_irrelevant",
            "retrieve_documents": "retrieve_documents",
        },
    )

    g.add_conditional_edges(
        "retrieve_documents",
        _route_after_retrieve,
        {
            "handle_not_found":    "handle_not_found",
            "generate_answer":     "generate_answer",
            "generate_summary":    "generate_summary",
            "format_schedule_link": "format_schedule_link",
        },
    )

    for terminal in (
        "handle_general",
        "handle_irrelevant",
        "handle_not_found",
        "generate_answer",
        "generate_summary",
        "format_schedule_link",
    ):
        g.add_edge(terminal, END)

    return g


@lru_cache(maxsize=1)
def get_graph():
    """컴파일된 그래프를 싱글톤으로 반환한다."""
    return _build_graph().compile()

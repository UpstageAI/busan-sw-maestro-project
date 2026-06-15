"""resolve_goal 노드 — 목표 클래스를 분류하고, 막연한 질문이면 다음 목표를 제안한다.

`analyze` 직후(마인크래프트 도메인 한정) 실행된다. 사용자가 목표를 분명히 밝혔으면
그 목표를 정리하고, "이제 뭐하지?"처럼 막연하면 현재 인벤토리·게임 상태를 근거로
구체적인 다음 목표를 하나 제안한다. 제안된 목표는 결정론 제작 분석(check_materials)과
코치 응답(format_goal_block)에 반영된다.

LLM 호출이 실패하면 빈 업데이트를 반환해 기존 흐름(되묻기·RAG·응답)을 유지한다.
"""
import logging

from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas import AgentState, GoalResolution
from app.core.llm import get_llm
from app.knowledge.minecraft_facts import item_ko
from app.prompts.templates import (
    GOAL_RESOLVER_SYSTEM,
    format_inventory_block,
    format_game_state_block,
)

logger = logging.getLogger(__name__)


def resolve_goal(state: AgentState) -> dict:
    """목표 클래스(craft/survival/explore/vague)를 분류하고, 막연하면 다음 목표를 제안한다."""
    query = state["query"]
    history = state.get("history_text", "")
    hist_block = f"[이전 대화]\n{history}\n\n" if history else ""
    prior = state.get("prior_goal_key", "")
    prior_block = f"[직전 목표] {item_ko(prior)}\n\n" if prior else ""
    inv_block = format_inventory_block(state.get("inventory", []), state.get("inventory_connected", False))
    state_block = format_game_state_block(state.get("game_state", {}))
    user_content = f"{hist_block}{prior_block}{state_block}{inv_block}[현재 질문] {query}"

    try:
        structured_llm = get_llm(temperature=0.0).with_structured_output(GoalResolution)
        r = structured_llm.invoke([
            SystemMessage(content=GOAL_RESOLVER_SYSTEM),
            HumanMessage(content=user_content),
        ])
        logger.info("RESOLVE_GOAL: class=%s proposed=%s goal=%s", r.goal_class, r.proposed, r.goal_text)
        return {
            "goal_class": r.goal_class,
            "resolved_goal": r.goal_text,
            "goal_proposed": r.proposed,
        }
    except Exception as e:
        logger.warning("Goal resolution failed: %s", e)
        return {}

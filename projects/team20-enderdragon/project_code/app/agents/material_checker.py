"""check_materials 노드 — 제작 목표를 해석해 결정론적으로 부족 재료를 점검한다.

먼저 사용자 질문에서 제작 목표 아이템을 찾고, 없으면 resolve_goal이 제안한 목표
문장(resolved_goal)에서 찾는다. 막연한 질문("뭐하지?")에 제안된 제작 목표도 검증된
부족 재료·채굴 티어로 안내하기 위함이다. 찾으면 plan_materials 결과를 상태에 싣고,
responder가 이를 프롬프트에 주입해 검증된 수치로 안내한다.
제작 목표가 없으면(생존·탐험 등) 아무것도 하지 않고 기존 흐름을 유지한다.
"""
import logging

from app.schemas import AgentState
from app.knowledge import planner, recipes
from app.knowledge.goal_resolver import resolve_craft_target

logger = logging.getLogger(__name__)


def check_materials(state: AgentState) -> dict:
    # 사용자 질문을 우선, 없으면 resolve_goal이 제안한 목표 문장에서 제작 대상을 찾는다.
    target = resolve_craft_target(state.get("query", "")) or resolve_craft_target(state.get("resolved_goal", ""))
    if not target:
        return {}
    material_plan = planner.plan_materials(target, state.get("inventory", []))
    logger.info("CHECK_MATERIALS: target=%s ready=%s gather=%d",
                target, material_plan["ready"], len(material_plan["gather"]))
    out = {"goal_key": target, "material_plan": material_plan}
    # 제작법 격자(3×3 배치) — 모드 GUI가 아이콘으로 렌더링. shaped 레시피만 존재.
    grid = recipes.recipe_grid(target)
    if grid:
        out["recipe"] = grid
    return out

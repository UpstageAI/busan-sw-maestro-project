"""세션 진척도 load/persist 노드 — 멀티턴 기억의 백본.

`load_state`는 그래프 시작에서 직전 진척도(목표·인벤토리)를 불러오고,
`persist_state`는 종료 전에 이번 턴 상태를 저장한다. 다음 턴이 직전 맥락을 이어받게 한다.
DB 장애는 best-effort로 무시한다(코칭은 계속 동작).
"""
import logging

from app.schemas import AgentState
from app.core.database import SessionLocal
from app.knowledge import planner
from app import repositories

logger = logging.getLogger(__name__)


def load_state(state: AgentState) -> dict:
    """직전 턴의 진척도 스냅샷을 불러온다(목표·인벤토리·plan·완료 단계)."""
    thread_id = state.get("thread_id")
    if not thread_id:
        return {}
    try:
        with SessionLocal() as db:
            snapshot = repositories.get_coaching_state(db, thread_id) or {}
    except Exception as e:
        logger.warning("load_state 실패(무시): %s", e)
        return {}
    return {
        "prior_goal_key": snapshot.get("goal_key", ""),
        "prior_last_inventory": snapshot.get("last_inventory", []),
        "prior_plan": snapshot.get("plan", []),
        "prior_completed": snapshot.get("completed", []),
    }


def reconcile(state: AgentState) -> dict:
    """직전 진척도와 현재 상태를 견줘 진행을 인식한다.

    1) 인벤토리 델타로 '새로 얻은 재료'(progress_note)를 집어낸다.
    2) 같은 목표를 이어가는 중이면, 직전 plan 단계 중 이제 더 필요 없어진 것을
       '완료한 단계'(completed_steps)로 가려내고 누적(goal_completed)한다.
    3) 현재 plan에서 결정론으로 '다음 한 단계'(next_step)를 고른다.
    responder가 이들로 진행을 칭찬하고 다음 행동을 콕 집어 안내한다.
    """
    out: dict = {}

    # 1) 인벤토리 델타 — 새로 얻은 재료
    prior_inv = {i["item"]: i["count"] for i in state.get("prior_last_inventory", [])}
    if prior_inv:
        current = {i["item"]: i["count"] for i in state.get("inventory", [])}
        gained = [
            {"item": item, "count": count - prior_inv.get(item, 0)}
            for item, count in current.items()
            if count > prior_inv.get(item, 0)
        ]
        if gained:
            out["progress_note"] = gained

    goal = state.get("goal_key")
    plan = state.get("material_plan") or {}
    if not goal or not plan:
        return out  # 제작 목표가 없으면(생존·탐험 등) 단계 추적은 생략

    # 2) 목표 진행 — 직전 plan 대비 완료 단계 (같은 목표를 이어갈 때만)
    completed = list(state.get("prior_completed", [])) if state.get("prior_goal_key") == goal else []
    cur_needs = {g["item"] for g in plan.get("gather", [])}
    newly_done = [
        step["item"] for step in state.get("prior_plan", [])
        if state.get("prior_goal_key") == goal and step["item"] not in cur_needs and step["item"] not in completed
    ]
    for item in newly_done:
        completed.append(item)
    if newly_done:
        out["completed_steps"] = newly_done
    out["goal_completed"] = completed

    # 3) 다음 한 단계
    nxt = planner.next_action(plan)
    if nxt:
        out["next_step"] = nxt
    return out


def persist_state(state: AgentState) -> dict:
    """이번 턴의 목표·인벤토리·plan·완료 단계를 저장한다(없으면 직전 값 유지)."""
    thread_id = state.get("thread_id")
    if not thread_id:
        return {}
    # 게임 모드면 현재 인벤토리를 저장, 웹이면 직전 값을 유지(웹은 인벤토리 없음).
    last_inventory = state["inventory"] if state.get("inventory_connected") else state.get("prior_last_inventory", [])
    # 제작 목표가 있으면 이번 plan 단계를 저장, 없으면(되묻기·비제작) 직전 plan을 유지.
    if state.get("goal_key"):
        plan = [{"item": g["item"], "qty": g["qty"]}
                for g in (state.get("material_plan") or {}).get("gather", [])]
    else:
        plan = state.get("prior_plan", [])
    snapshot = {
        "goal_key": state.get("goal_key") or state.get("prior_goal_key", ""),
        "last_inventory": last_inventory,
        "plan": plan,
        "completed": state.get("goal_completed", state.get("prior_completed", [])),
    }
    try:
        with SessionLocal() as db:
            repositories.upsert_coaching_state(db, thread_id, snapshot)
    except Exception as e:
        logger.warning("persist_state 실패(무시): %s", e)
    return {}

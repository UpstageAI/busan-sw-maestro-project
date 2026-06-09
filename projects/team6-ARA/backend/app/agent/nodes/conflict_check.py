"""Duplicate / Conflict Check 노드.

선택된 항목을 기존 저장소(calendar_events / tasks)와 대조한다.
calendar / task 만 검사하고 memo / risk / pending 은 통과한다.
결과를 ReviewableItem(item+selection+conflict) 으로 묶어 /route 응답을 구성한다.
"""

from app.conflict.rules import check_conflict
from app.logging_config import get_logger
from app.schemas.items import Item
from app.schemas.routing import ConflictCheckResult, ReviewableItem, ToolSelection
from app.storage.queries import load_calendar_events, load_tasks

logger = get_logger("node.conflict_check")


def conflict_check_node(state: dict) -> dict:
    """state["items"] + selections -> conflicts / reviewables."""
    items = {it["id"]: Item.model_validate(it) for it in state.get("items", [])}
    selections = [ToolSelection.model_validate(s) for s in state.get("selections", [])]

    calendar_events = load_calendar_events()
    tasks = load_tasks()
    logger.info(
        "분기: conflict_check 시작 - selections=%d stored_calendar=%d stored_tasks=%d",
        len(selections),
        len(calendar_events),
        len(tasks),
    )

    conflicts: list[dict] = []
    reviewables: list[dict] = []
    conflict_count = 0
    for sel in selections:
        item = items.get(sel.item_id)
        if item is None:
            logger.debug("선택 항목에 대응하는 item 없음: %s", sel.item_id)
            continue
        result: ConflictCheckResult = check_conflict(item, calendar_events, tasks)
        conflicts.append(result.model_dump(mode="json"))
        if result.has_conflict:
            conflict_count += 1
            logger.warning(
                "conflict_check: conflict item=%s kind=%s warning=%s",
                sel.item_id,
                result.kind,
                result.warning,
            )
        else:
            logger.debug("conflict_check: no conflict item=%s type=%s", sel.item_id, item.type)
        reviewables.append(
            ReviewableItem(
                item=item, selection=sel, conflict=result
            ).model_dump(mode="json")
        )

    logger.info(
        "분기: conflict_check 완료 - 검토 %d건, 충돌 %d건",
        len(reviewables),
        conflict_count,
    )
    return {"conflicts": conflicts, "reviewables": reviewables}

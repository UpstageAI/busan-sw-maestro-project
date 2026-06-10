"""Tool Selection 노드.

6-1 항목(type)을 기준으로 recommended_tool 을 규칙 매핑한다 (LLM 미사용).
type=ignore 는 처리 대상에서 제외(skipped)한다.
"""

from app.logging_config import get_logger, summarize_items
from app.schemas.items import Item, ItemType, ToolName
from app.schemas.routing import ToolSelection

logger = get_logger("node.tool_selection")

# type -> Tool 규칙 매핑 (planning.md 6-2).
TYPE_TO_TOOL: dict[ItemType, ToolName] = {
    ItemType.task: ToolName.create_task,
    ItemType.calendar: ToolName.create_calendar_event,
    ItemType.memo: ToolName.create_memo,
    ItemType.risk: ToolName.create_risk_log,
    ItemType.pending: ToolName.save_to_pending,
}

_ROUTING_REASON: dict[ItemType, str] = {
    ItemType.task: "할 일 항목 -> 작업 생성",
    ItemType.calendar: "일정 항목 -> 캘린더 이벤트 생성",
    ItemType.memo: "메모 항목 -> 메모 저장",
    ItemType.risk: "리스크 항목 -> 리스크 로그 기록",
    ItemType.pending: "정보 부족 항목 -> Pending 보류",
}


def select_tool(item: Item) -> ToolSelection | None:
    """단일 항목의 Tool 을 선택한다. ignore 면 None."""
    if item.type == ItemType.ignore:
        return None
    tool = TYPE_TO_TOOL[item.type]
    return ToolSelection(
        item_id=item.id or "",
        selected_tool=tool,
        routing_reason=_ROUTING_REASON[item.type],
    )


def tool_selection_node(state: dict) -> dict:
    """state["items"] -> selections / skipped / 정규화된 items."""
    raw_items = state.get("items", [])
    logger.info("분기: tool_selection 시작 - %s", summarize_items(raw_items))
    items: list[Item] = [
        Item.model_validate(it).ensure_id(idx) for idx, it in enumerate(raw_items)
    ]

    selections: list[dict] = []
    skipped: list[dict] = []
    for item in items:
        sel = select_tool(item)
        if sel is None:
            logger.debug("tool_selection: skipped item=%s type=%s title=%s", item.id, item.type, item.title)
            skipped.append(item.model_dump(mode="json"))
            continue
        logger.debug(
            "tool_selection: item=%s type=%s -> tool=%s",
            item.id,
            item.type,
            sel.selected_tool,
        )
        selections.append(sel.model_dump(mode="json"))

    logger.info(
        "분기: tool_selection 완료 - 대상 %d건, 제외 %d건",
        len(selections),
        len(skipped),
    )
    return {
        "items": [i.model_dump(mode="json") for i in items],
        "selections": selections,
        "skipped": skipped,
    }

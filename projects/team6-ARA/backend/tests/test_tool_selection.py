"""Tool Selection 노드 단위 테스트."""

import pytest

from app.agent.nodes.tool_selection import TYPE_TO_TOOL, select_tool, tool_selection_node
from app.schemas.items import Item, ItemType, ToolName


@pytest.mark.parametrize(
    ("item_type", "expected_tool"),
    [
        (ItemType.task, ToolName.create_task),
        (ItemType.calendar, ToolName.create_calendar_event),
        (ItemType.memo, ToolName.create_memo),
        (ItemType.risk, ToolName.create_risk_log),
        (ItemType.pending, ToolName.save_to_pending),
    ],
)
def test_type_to_tool_mapping(item_type, expected_tool):
    item = Item(id="x", type=item_type, title="제목")
    sel = select_tool(item)
    assert sel is not None
    assert sel.selected_tool == expected_tool
    assert sel.routing_reason  # 근거는 비어 있지 않다


def test_ignore_is_not_selected():
    item = Item(id="x", type=ItemType.ignore, title="잡담")
    assert select_tool(item) is None


def test_node_splits_selected_and_skipped():
    state = {
        "items": [
            {"type": "task", "title": "A"},
            {"type": "ignore", "title": "B"},
            {"type": "calendar", "title": "C", "date": "2026-06-09", "time": "10:00"},
        ]
    }
    out = tool_selection_node(state)
    assert len(out["selections"]) == 2
    assert len(out["skipped"]) == 1
    # id 가 없으면 인덱스 기반으로 부여된다
    ids = [it["id"] for it in out["items"]]
    assert ids == ["item-0", "item-1", "item-2"]


def test_all_types_are_mapped():
    # ignore 를 제외한 모든 type 이 매핑돼 있다
    mapped = set(TYPE_TO_TOOL.keys())
    assert mapped == set(ItemType) - {ItemType.ignore}

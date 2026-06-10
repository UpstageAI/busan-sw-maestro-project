"""Local Tool 레지스트리.

execution_node 는 TOOL_REGISTRY[selected_tool] 로 실제 함수를 찾아 호출한다.
"""

from collections.abc import Callable

from app.schemas.items import ToolName
from app.tools.local_tools import (
    create_calendar_event,
    create_memo,
    create_risk_log,
    create_task,
    save_to_pending,
)

TOOL_REGISTRY: dict[ToolName, Callable[..., int]] = {
    ToolName.create_task: create_task,
    ToolName.create_calendar_event: create_calendar_event,
    ToolName.create_memo: create_memo,
    ToolName.create_risk_log: create_risk_log,
    ToolName.save_to_pending: save_to_pending,
}

__all__ = [
    "TOOL_REGISTRY",
    "create_task",
    "create_calendar_event",
    "create_memo",
    "create_risk_log",
    "save_to_pending",
]

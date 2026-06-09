"""6-2 라우팅/검증/승인 도메인 스키마.

- items: 6-1 분석 출력(= 6-2 입력) 항목 모델
- routing: Tool 선택 / 충돌 검사 / 검토 패키지
- approval: 사용자 승인 결정 / Tool 실행 결과

전송(요청/응답) 모델은 그래프/엔드포인트 레이어(agent-api)에서 정의한다.
"""

from app.schemas.approval import (
    ApprovalAction,
    ApprovalDecision,
    ExecutionResult,
    ExecutionStatus,
)
from app.schemas.items import Item, ItemType, Priority, ToolName
from app.schemas.routing import (
    ConflictAlternative,
    ConflictCheckResult,
    ConflictKind,
    ReviewableItem,
    ToolSelection,
)

__all__ = [
    # items
    "Item",
    "ItemType",
    "Priority",
    "ToolName",
    # routing
    "ConflictAlternative",
    "ConflictCheckResult",
    "ConflictKind",
    "ReviewableItem",
    "ToolSelection",
    # approval
    "ApprovalAction",
    "ApprovalDecision",
    "ExecutionResult",
    "ExecutionStatus",
]

"""사용자 승인 결정 / Tool 실행 결과 도메인 스키마."""

from enum import Enum

from pydantic import BaseModel

from app.schemas.items import Item, ToolName


class ApprovalAction(str, Enum):
    approve = "approve"  # 승인 -> Tool 실행 + 저장
    modify = "modify"  # 수정 -> 저장 안 함, 재검증 신호
    exclude = "exclude"  # 제외 -> 저장 안 함


class ApprovalDecision(BaseModel):
    """항목 단위 사용자 결정 (승인 interrupt 의 resume 입력)."""

    item_id: str
    action: ApprovalAction
    modified_item: Item | None = None  # action=modify 일 때 수정된 항목


class ExecutionStatus(str, Enum):
    success = "success"
    failed = "failed"
    excluded = "excluded"
    needs_recheck = "needs_recheck"  # modify -> 재검증 필요
    pending = "pending"  # Tool 실패 -> Pending 폴백


class ExecutionResult(BaseModel):
    """항목 단위 Tool 실행 결과."""

    item_id: str
    status: ExecutionStatus
    tool: ToolName | None = None
    stored_id: int | None = None  # 저장된 레코드 PK
    error: str | None = None
    recheck_required: bool = False  # modify 항목의 재검증 신호
    modified_item: Item | None = None  # 재투입용 echo (modify)

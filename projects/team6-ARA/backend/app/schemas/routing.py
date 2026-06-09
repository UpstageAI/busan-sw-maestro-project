"""Tool 선택 / 중복,충돌 검사 / /route 응답 스키마."""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.items import Item, ToolName


class ToolSelection(BaseModel):
    """type -> Tool 매핑 결과. routing_reason 은 화면 표시용 근거."""

    item_id: str
    selected_tool: ToolName
    routing_reason: str


class ConflictKind(str, Enum):
    none = "none"
    calendar_overlap = "calendar_overlap"
    task_duplicate = "task_duplicate"


class ConflictAlternative(str, Enum):
    """충돌 시 제안하는 대체 경로 (제안만, 자동 실행 없음)."""

    merge = "merge"
    modify = "modify"
    pending = "pending"


class ConflictCheckResult(BaseModel):
    """기존 저장소 대조 결과."""

    item_id: str
    kind: ConflictKind = ConflictKind.none
    has_conflict: bool = False
    conflicting_with: list[dict] = Field(default_factory=list)  # 기존 레코드 요약
    warning: str | None = None
    suggested_alternatives: list[ConflictAlternative] = Field(default_factory=list)


class ReviewableItem(BaseModel):
    """사용자 검토용 항목 단위 패키지 (승인 단계 입력 구성요소)."""

    item: Item
    selection: ToolSelection
    conflict: ConflictCheckResult

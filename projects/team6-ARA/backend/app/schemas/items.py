"""6-1 분석 출력 항목 모델 (= 6-2 라우팅의 입력).

6-1 `/analyze/`는 이 스키마를 최종 출력으로 사용하고, 6-2는 같은 Item을
라우팅/충돌검사/승인 입력으로 받는다.
"""

from datetime import date as _date  # 필드명 date 와 타입 충돌 방지
from enum import Enum

from pydantic import BaseModel


class ItemType(str, Enum):
    """항목 유형 (6-1 Classification 결과)."""

    task = "task"
    calendar = "calendar"
    memo = "memo"
    risk = "risk"
    pending = "pending"
    ignore = "ignore"


class ToolName(str, Enum):
    """Local Tool 식별자 (Tool Selection 결과)."""

    create_task = "create_task"
    create_calendar_event = "create_calendar_event"
    create_memo = "create_memo"
    create_risk_log = "create_risk_log"
    save_to_pending = "save_to_pending"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Item(BaseModel):
    """6-1이 산출한 단일 실행 항목.

    id 는 승인 단계에서 항목을 지목하기 위한 안정 식별자다.
    6-1이 부여하지 않으면 /route 가 `item-{idx}` 형태로 채운다.
    """

    id: str | None = None
    type: ItemType
    title: str

    # task / calendar 공통 메타
    assignee: str | None = None
    due_date: _date | None = None  # task 기준 마감일
    date: _date | None = None  # calendar 기준 일자
    time: str | None = None  # "HH:MM" (calendar)
    all_day: bool = False
    duration_estimate: int | None = None  # 분 단위 (calendar 충돌 검사용)
    priority: Priority = Priority.medium

    # memo / risk 본문
    content: str | None = None  # memo 내용
    description: str | None = None  # risk 설명
    mitigation: str | None = None  # risk 대응 방안

    # 6-1 판단 메타
    confidence: float = 1.0
    needs_confirmation: bool = False
    recommended_tool: ToolName | None = None  # 6-1이 줄 수도, 6-2가 채움
    source_sentence: str | None = None

    # pending 전용
    clarification_question: str | None = None

    model_config = {"use_enum_values": False}

    def ensure_id(self, index: int) -> "Item":
        """id 가 없으면 인덱스 기반으로 부여한 사본을 돌려준다."""
        if self.id:
            return self
        return self.model_copy(update={"id": f"item-{index}"})


# Tool 호출에 필요한 필수 필드 (경량 재검증용).
REQUIRED_FIELDS: dict[ItemType, tuple[str, ...]] = {
    ItemType.task: ("title",),
    ItemType.calendar: ("title", "date"),
    ItemType.memo: ("title",),
    ItemType.risk: ("title",),  # description 없으면 title 로 대체
    ItemType.pending: ("title",),
}

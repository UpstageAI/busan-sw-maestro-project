"""6-1 분석 내부 스키마.

최종 출력 Item 계약은 6-2 정본인 `app.schemas.items.Item`을 사용한다.
이 모듈은 Solar/FakeLLM raw JSON 검증과 `/analyze` 응답 래퍼만 담당한다.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.items import Item

# LLM이 직접 분류하는 실질 유형 4종. pending/ignore는 코드가 후처리한다.
ItemType = Literal["task", "calendar", "memo", "risk"]
ToolName = Literal[
    "create_task", "create_calendar_event", "create_memo",
    "create_risk_log", "save_to_pending",   # save_to_pending은 6-2가 확인 필요 항목에 사용
]
Priority = Literal["high", "medium", "low"]
DateStatus = Literal["concrete", "vague", "missing"]

# 코드 enum → 화면 한글 라벨 (None/미분류는 호출부에서 기본값 처리)
LABELS: dict[str, str] = {
    "task": "할 일", "calendar": "일정", "memo": "메모", "risk": "리스크",
}


class ContextBundle(BaseModel):
    """Context Loader 결과 (선호/지침/기존 항목 요약)."""
    preferences: list[dict] = Field(default_factory=list)
    guidelines: list[dict] = Field(default_factory=list)
    existing_items_summary: str = ""


class LLMItem(BaseModel):
    """LLM(Solar)이 항목별로 내놓는 원본. 점수는 LLM이 매기지 않고 플래그만 준다."""
    type: ItemType
    title: str
    assignee: str | None = None
    date: str | None = None          # "YYYY-MM-DD"
    time: str | None = None          # "HH:MM" (KST)
    priority: Priority = "medium"
    source_sentence: str = ""
    recommended_tool: ToolName | None = None   # 6-1 힌트, 6-2가 확정(D5)

    # 판단 플래그 (planning.md confidence 절)
    type_certainty: float = 1.0
    date_status: DateStatus = "concrete"
    assignee_present: bool = False
    time_present: bool = False
    needs_base_event: bool = False
    required_ok: bool = True


class LLMOutput(BaseModel):
    """Solar 응답 전체. pipeline이 이걸로 검증한다. 실행 항목 없으면 items=[]."""
    items: list[LLMItem] = Field(default_factory=list)


class AnalyzeResult(BaseModel):
    """POST /analyze 응답. items=[] 이면 실행 항목 없음(요약만)."""
    items: list[Item] = Field(default_factory=list)

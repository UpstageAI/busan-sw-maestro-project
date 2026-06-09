"""단일 그래프 전송(요청/응답) 모델.

도메인 모델(Item/ReviewableItem/ApprovalDecision/ExecutionResult)은 schemas 의 다른
모듈에서 재사용하고, 여기서는 /run, /resume 의 HTTP 입출력만 정의한다.
"""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.approval import ApprovalDecision, ExecutionResult
from app.schemas.items import Item
from app.schemas.routing import ReviewableItem


class RunStatus(str, Enum):
    awaiting_approval = "awaiting_approval"  # interrupt - 사용자 결정 대기
    completed = "completed"  # 그래프 종료


class RunRequest(BaseModel):
    """POST /run 요청. items 는 /analyze/ 출력 Item. session_id 가 thread_id."""

    session_id: str
    items: list[Item] = Field(default_factory=list)
    raw_input: str | None = None  # 향후 /run 직접 분석 확장 자리


class ResumeRequest(BaseModel):
    """POST /resume 요청. 승인 interrupt 에 대한 사용자 결정."""

    session_id: str
    decisions: list[ApprovalDecision]


class RunResponse(BaseModel):
    """/run, /resume 공통 응답.

    - status=awaiting_approval: reviewables/skipped 를 보고 사용자가 결정 -> /resume
    - status=completed: results/summary/final_output 가 채워짐
    """

    session_id: str
    status: RunStatus
    # awaiting_approval 일 때
    reviewables: list[ReviewableItem] = Field(default_factory=list)
    skipped: list[Item] = Field(default_factory=list)
    # completed 일 때
    results: list[ExecutionResult] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    final_output: dict | None = None

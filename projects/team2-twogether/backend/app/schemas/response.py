"""/recommend 응답 스키마.

프론트엔드 계약(`frontend/src/types/api.ts`)과 1:1로 맞춘다. 응답은 ``status``
하나로 화면 분기가 결정되는 3종 형태이며, result_builder 가 만드는 페이로드를
그대로 직렬화/검증할 수 있다.

  - need_clarification → 확인 질문 (노드 1이 생성)
  - recommended        → 정상 추천 (result_builder)
  - limited            → 근거 제한적 추천 (result_builder)
"""

from typing import List, Literal, Union

from pydantic import BaseModel, Field


class MentorCard(BaseModel):
    """추천 결과 카드 한 건. 프론트 ``Mentor`` 와 동일 필드."""

    name: str
    domain: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    score: int  # 적합도 0~100 (카드 표시용 정수)
    reason: str  # 추천 이유 (백엔드 생성 텍스트 그대로 — 환각 방지)
    can_help: List[str] = Field(default_factory=list)
    less_relevant_for: List[str] = Field(default_factory=list)
    profile_summary: str = ""


class RecommendedResponse(BaseModel):
    """정상 추천 → 결과 화면(S-04)."""

    status: Literal["recommended"]
    gaps: List[str] = Field(default_factory=list)
    refined: bool = False  # 재검색이 일어났는지
    mentors: List[MentorCard] = Field(default_factory=list)


class LimitedResponse(BaseModel):
    """재검색 후에도 근거가 약한 추천 → 결과 화면 + 제한 배너."""

    status: Literal["limited"]
    gaps: List[str] = Field(default_factory=list)
    mentors: List[MentorCard] = Field(default_factory=list)
    notice: str  # 제한적 추천 안내 (그대로 표시)


class ClarificationResponse(BaseModel):
    """입력 부족 → 확인 질문(S-03)."""

    status: Literal["need_clarification"]
    question: str
    options: List[str] = Field(default_factory=list)


#: /recommend 응답 유니온. status 로 구분(discriminated union).
RecommendResponse = Union[
    RecommendedResponse,
    LimitedResponse,
    ClarificationResponse,
]

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.schemas.gap import GapContext


class ClarificationAssessment(BaseModel):
    is_sufficient: bool
    question: str = ""
    options: list[str] = Field(default_factory=list)


class GapReview(BaseModel):
    gap_context: GapContext


class MentorIntentMatch(BaseModel):
    mentor_id: str
    intent_match: float = Field(ge=0.0, le=1.0)
    matched_needs: list[str] = Field(default_factory=list)


class MentorIntentReview(BaseModel):
    matches: list[MentorIntentMatch]

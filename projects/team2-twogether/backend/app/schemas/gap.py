from typing import Literal

from pydantic import BaseModel, Field


class ParsedInput(BaseModel):
    project_summary: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    current_stage: str = ""
    concerns: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    user_goal: str = ""


class GapContext(BaseModel):
    main_gap: str
    gap_categories: list[str]
    needed_mentor_expertise: list[str]
    priority: Literal["high", "medium", "low"]
    reason: str
    query_hints: list[str]
    source_fields: list[str]

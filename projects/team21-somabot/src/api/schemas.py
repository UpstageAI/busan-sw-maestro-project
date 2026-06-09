from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class SourceDocument(BaseModel):
    source: str
    preview: str  # 청크 앞 100자


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    intent: str
    sources: list[SourceDocument]
    execution_history: list[str]


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    last_active: str
    turn_count: int  # chat_history 길이 / 2


class ErrorResponse(BaseModel):
    detail: str

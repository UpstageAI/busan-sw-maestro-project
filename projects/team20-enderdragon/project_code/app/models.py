from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """서비스 사용자. 초기에는 익명/기본 유저 수준으로만 사용한다."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")


class ChatSession(Base):
    """대화 세션. thread_id로 식별하며 후속 질문의 맥락 단위가 된다."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    """세션 내 한 발화(사용자/어시스턴트)."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # 'user' | 'assistant' | 'clarification'(내부용)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

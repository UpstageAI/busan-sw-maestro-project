"""DB 데이터 접근 계층.

에이전트/엔드포인트는 DB 내부 구조를 몰라도 이 함수들만 호출하면 된다.
(팀원이 기능을 추가할 때 사용하는 공용 인터페이스)
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatSession, Message


def get_or_create_session(db: Session, thread_id: str, user_id: int | None = None) -> ChatSession:
    """thread_id로 세션을 찾고, 없으면 새로 만든다."""
    session = db.scalar(select(ChatSession).where(ChatSession.thread_id == thread_id))
    if session is None:
        session = ChatSession(thread_id=thread_id, user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def append_message(db: Session, session_id: int, role: str, content: str) -> Message:
    """세션에 메시지 한 건(role: 'user' | 'assistant')을 추가한다."""
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(db: Session, session_id: int, limit: int = 20) -> list[Message]:
    """세션의 최근 메시지를 시간순(오래된 → 최신)으로 반환한다."""
    rows = db.scalars(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))


def list_sessions(db: Session, limit: int = 30) -> list[tuple[ChatSession, str]]:
    """최근 세션 목록과 각 세션의 첫 번째 사용자 메시지(미리보기)를 반환한다."""
    sessions = db.scalars(
        select(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .limit(limit)
    ).all()
    result = []
    for session in sessions:
        first_msg = db.scalar(
            select(Message)
            .where(Message.session_id == session.id, Message.role == "user")
            .order_by(Message.created_at.asc())
            .limit(1)
        )
        preview = first_msg.content if first_msg else "(빈 대화)"
        result.append((session, preview))
    return result


def get_session_by_thread(db: Session, thread_id: str) -> ChatSession | None:
    """thread_id로 세션을 조회한다."""
    return db.scalar(select(ChatSession).where(ChatSession.thread_id == thread_id))


def delete_session(db: Session, thread_id: str) -> bool:
    """세션과 관련 메시지를 삭제한다 (cascade). 성공하면 True."""
    session = get_session_by_thread(db, thread_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...session.manager import session_manager
from ..schemas import SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session():
    session = session_manager.create()
    return _to_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    session = session_manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다.")
    return _to_response(session)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str):
    session_manager.delete(session_id)


def _to_response(session) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        last_active=session.last_active.isoformat(),
        turn_count=len(session.chat_history) // 2,
    )

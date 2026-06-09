from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta

from .models import Session
from ..config import get_settings


class SessionManager:
    """인메모리 세션 저장소. 스레드 안전."""

    def __init__(self) -> None:
        self._store: dict[str, Session] = {}
        self._lock = threading.Lock()

    # ── CRUD ──────────────────────────────────────────────────────────

    def create(self) -> Session:
        session = Session(session_id=str(uuid.uuid4()))
        with self._lock:
            self._store[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._store.get(session_id)
        if session and self._is_expired(session):
            self.delete(session_id)
            return None
        return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    # ── 만료 정리 ──────────────────────────────────────────────────────

    def _is_expired(self, session: Session) -> bool:
        ttl = timedelta(minutes=get_settings().session_ttl_minutes)
        return datetime.utcnow() - session.last_active > ttl

    def purge_expired(self) -> int:
        """만료된 세션을 삭제하고 삭제 개수를 반환한다."""
        expired = [sid for sid, s in self._store.items() if self._is_expired(s)]
        with self._lock:
            for sid in expired:
                self._store.pop(sid, None)
        return len(expired)


# 앱 전역 단일 인스턴스
session_manager = SessionManager()

"""SQLite 저장소 (6-2 Tool 실행 결과 + 충돌 검사용 기존 데이터).

경로 결정 순서:
  1. configure_db_path() 로 명시 설정된 값
  2. 환경변수 ACTION_ROUTER_DB_PATH
  3. 기본값 backend/storage.db

테스트는 configure_db_path() 또는 env var 로 tmp DB 를 주입해 실제 파일 오염을 막는다.
스키마 생성 패턴은 feat/preferences 의 feedback/db.py 멱등 executescript 를 모방한다.
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "storage.db"
_configured_path: Path | None = None

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS tasks (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT NOT NULL,
        assignee   TEXT,
        due_date   TEXT,
        priority   TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS calendar_events (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        title              TEXT NOT NULL,
        date               TEXT,
        time               TEXT,
        all_day            INTEGER NOT NULL DEFAULT 0,
        duration_estimate  INTEGER,
        created_at         TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS memos (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT NOT NULL,
        content    TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS risk_logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        mitigation  TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS pending_queue (
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        title                  TEXT NOT NULL,
        reason                 TEXT,
        clarification_question TEXT,
        created_at             TEXT NOT NULL DEFAULT (datetime('now'))
    );
"""

# kind -> table 매핑 (GET /storage/{kind} 에서 사용).
TABLES: dict[str, str] = {
    "tasks": "tasks",
    "calendar_events": "calendar_events",
    "memos": "memos",
    "risk_logs": "risk_logs",
    "pending_queue": "pending_queue",
}


def configure_db_path(path: str | Path | None) -> None:
    """DB 경로를 명시 설정한다 (테스트 훅). None 이면 기본/환경변수로 복귀."""
    global _configured_path
    _configured_path = Path(path) if path is not None else None


def db_path() -> Path:
    if _configured_path is not None:
        return _configured_path
    env = os.environ.get("ACTION_ROUTER_DB_PATH")
    if env:
        return Path(env)
    return _DEFAULT_DB_PATH


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """스키마가 보장된 커넥션을 컨텍스트로 돌려준다 (멱등).

    sqlite3.Connection 자체를 `with` 로 쓰면 commit/rollback 만 하고 close 는
    하지 않아 호출마다 커넥션이 누수된다. 여기서 finally 로 명시 close 하므로
    `with get_conn() as conn:` 호출은 블록 종료 시 항상 닫힌다.
    쓰기 함수는 블록 안에서 conn.commit() 을 명시 호출해야 한다(여기선 자동 커밋 안 함).
    """
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """스키마만 생성하고 닫는다 (앱 startup / 테스트 fixture 용)."""
    with get_conn():
        pass

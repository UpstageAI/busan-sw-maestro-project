import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parent.parent.parent / "feedback.db"


@contextmanager
def _get_conn() -> Iterator[sqlite3.Connection]:
    """스키마가 보장된 커넥션을 컨텍스트로 돌려준다 (멱등).

    sqlite3.Connection 자체를 `with` 로 쓰면 commit/rollback 만 하고 close 는
    하지 않아 호출마다 커넥션이 누수된다. 여기서 finally 로 명시 close 한다.
    쓰기 함수는 블록 안에서 conn.commit() 을 명시 호출해야 한다(여기선 자동 커밋 안 함).
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS preference_candidate_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT NOT NULL,
            original     TEXT NOT NULL,
            modified     TEXT NOT NULL,
            diff         TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            candidates   TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS user_preference (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            field            TEXT NOT NULL,
            original_pattern TEXT NOT NULL,
            preferred        TEXT NOT NULL,
            created_at       TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(field, original_pattern)
        );
    """)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def save_candidate_log(
    session_id: str,
    original: dict[str, Any],
    modified: dict[str, Any],
    diff: dict[str, Any],
    pattern_type: str,
    candidates: list[dict[str, Any]],
) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO preference_candidate_log
               (session_id, original, modified, diff, pattern_type, candidates)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                json.dumps(original, ensure_ascii=False),
                json.dumps(modified, ensure_ascii=False),
                json.dumps(diff, ensure_ascii=False),
                pattern_type,
                json.dumps(candidates, ensure_ascii=False),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def save_user_preference(field: str, original_pattern: Any, preferred: Any) -> None:
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO user_preference (field, original_pattern, preferred)
               VALUES (?, ?, ?)
               ON CONFLICT(field, original_pattern)
               DO UPDATE SET preferred = excluded.preferred""",
            (
                field,
                json.dumps(original_pattern, ensure_ascii=False),
                json.dumps(preferred, ensure_ascii=False),
            ),
        )
        conn.commit()


def get_candidate_log(log_id: int) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT session_id, original, modified, pattern_type FROM preference_candidate_log WHERE id = ?",
            (log_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "session_id": row[0],
        "original": json.loads(row[1]),
        "modified": json.loads(row[2]),
        "pattern_type": row[3],
    }


def load_user_preferences() -> list[dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT field, original_pattern, preferred FROM user_preference"
        ).fetchall()
    return [
        {
            "field": row[0],
            "original_pattern": json.loads(row[1]),
            "preferred": json.loads(row[2]),
        }
        for row in rows
    ]

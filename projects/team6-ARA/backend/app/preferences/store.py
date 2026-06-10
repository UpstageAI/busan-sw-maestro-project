import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parent.parent.parent / "preferences.db"


@contextmanager
def _get_conn() -> Iterator[sqlite3.Connection]:
    """스키마가 보장된 커넥션을 컨텍스트로 돌려준다 (멱등).

    sqlite3.Connection 자체를 `with` 로 쓰면 commit/rollback 만 하고 close 는
    하지 않아 호출마다 커넥션이 누수된다. 여기서 finally 로 명시 close 한다.
    쓰기 함수는 블록 안에서 conn.commit() 을 명시 호출해야 한다(여기선 자동 커밋 안 함).
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS preferences (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            original   TEXT NOT NULL,
            modified   TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def load_preferences() -> list[dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT original, modified FROM preferences ORDER BY id"
        ).fetchall()
    return [
        {"original": json.loads(row[0]), "modified": json.loads(row[1])}
        for row in rows
    ]


def save_preference(original: dict[str, Any], modified: dict[str, Any]) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO preferences (original, modified) VALUES (?, ?)",
            (json.dumps(original, ensure_ascii=False), json.dumps(modified, ensure_ascii=False)),
        )
        conn.commit()

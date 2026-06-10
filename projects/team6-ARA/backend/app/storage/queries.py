"""충돌 검사 / 저장소 조회용 읽기 쿼리."""

from typing import Any

from app.storage.db import TABLES, get_conn


def load_calendar_events() -> list[dict[str, Any]]:
    """캘린더 충돌 검사용 기존 일정 조회."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, date, time, all_day, duration_estimate "
            "FROM calendar_events"
        ).fetchall()
    return [dict(r) for r in rows]


def load_tasks() -> list[dict[str, Any]]:
    """Task 중복 검사용 기존 작업 조회."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, assignee, due_date, priority FROM tasks"
        ).fetchall()
    return [dict(r) for r in rows]


def list_table(kind: str) -> list[dict[str, Any]]:
    """GET /storage/{kind} 용 전체 행 조회."""
    table = TABLES.get(kind)
    if table is None:
        raise KeyError(kind)
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    return [dict(r) for r in rows]

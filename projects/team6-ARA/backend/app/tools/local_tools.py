"""Local Tool 함수 (SQLite INSERT 후 PK 반환).

planning.md 6-2 의 시그니처를 그대로 따른다. Mock 이지만 실제 SQLite 에 저장하므로
end-to-end 동작이 성립한다.
"""

from datetime import date

from app.storage.db import get_conn


def _to_text(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def create_task(
    title: str,
    assignee: str | None = None,
    due_date=None,
    priority: str | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, assignee, due_date, priority) "
            "VALUES (?, ?, ?, ?)",
            (title, assignee, _to_text(due_date), _to_text(priority)),
        )
        conn.commit()
        return cur.lastrowid


def create_calendar_event(
    title: str,
    date=None,
    time: str | None = None,
    all_day: bool = False,
    duration_estimate: int | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO calendar_events "
            "(title, date, time, all_day, duration_estimate) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, _to_text(date), time, 1 if all_day else 0, duration_estimate),
        )
        conn.commit()
        return cur.lastrowid


def create_memo(title: str, content: str | None = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO memos (title, content) VALUES (?, ?)",
            (title, content),
        )
        conn.commit()
        return cur.lastrowid


def create_risk_log(description: str, mitigation: str | None = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO risk_logs (description, mitigation) VALUES (?, ?)",
            (description, mitigation),
        )
        conn.commit()
        return cur.lastrowid


def save_to_pending(
    title: str,
    reason: str | None = None,
    clarification_question: str | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pending_queue (title, reason, clarification_question) "
            "VALUES (?, ?, ?)",
            (title, reason, clarification_question),
        )
        conn.commit()
        return cur.lastrowid

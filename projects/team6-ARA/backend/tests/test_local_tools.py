"""Local Tool 함수 단위 테스트 (실제 SQLite INSERT)."""

from app.storage.queries import list_table
from app.tools import (
    create_calendar_event,
    create_memo,
    create_risk_log,
    create_task,
    save_to_pending,
)


def test_create_task_inserts(tmp_db):
    pk = create_task("발표", "박성종", "2026-06-06", "high")
    assert isinstance(pk, int)
    rows = list_table("tasks")
    assert len(rows) == 1
    assert rows[0]["title"] == "발표"
    assert rows[0]["assignee"] == "박성종"


def test_create_calendar_event_inserts(tmp_db):
    pk = create_calendar_event("회의", "2026-06-09", "10:00", False, 60)
    assert isinstance(pk, int)
    rows = list_table("calendar_events")
    assert rows[0]["all_day"] == 0
    assert rows[0]["duration_estimate"] == 60


def test_create_memo_inserts(tmp_db):
    create_memo("메모제목", "내용")
    rows = list_table("memos")
    assert rows[0]["content"] == "내용"


def test_create_risk_log_inserts(tmp_db):
    create_risk_log("리스크 설명", "대응 방안")
    rows = list_table("risk_logs")
    assert rows[0]["mitigation"] == "대응 방안"


def test_save_to_pending_inserts(tmp_db):
    create = save_to_pending("보류 항목", "정보 부족", "언제인가요?")
    assert isinstance(create, int)
    rows = list_table("pending_queue")
    assert rows[0]["clarification_question"] == "언제인가요?"


def test_pk_increments(tmp_db):
    a = create_task("A")
    b = create_task("B")
    assert b == a + 1

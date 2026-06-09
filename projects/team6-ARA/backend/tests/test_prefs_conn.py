"""6-3 (feedback/preferences) DB 커넥션 누수 픽스 검증.

DB 격리는 conftest 의 autouse fixture(isolate_6_3_db)가 _DB_PATH 를 tmp 로 돌려 처리한다.
여기서는 누수 픽스(@contextmanager + finally close)와 명시 commit 영속만 검증한다.

검증 대상:
- _get_conn 이 @contextmanager 로 블록 종료 시 커넥션을 닫는다 (누수 방지).
- 쓰기 함수가 명시 commit 으로 영속된다 (자동 커밋 제거 후에도 영속 유지).
"""

import sqlite3

import pytest

from app.feedback import db as feedback_db
from app.preferences import store as pref_store


def test_feedback_conn_closed_after_block():
    with feedback_db._get_conn() as conn:
        conn.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_pref_conn_closed_after_block():
    with pref_store._get_conn() as conn:
        conn.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_save_candidate_log_persists():
    log_id = feedback_db.save_candidate_log(
        session_id="s1",
        original={"a": 1},
        modified={"a": 2},
        diff={"a": [1, 2]},
        pattern_type="one_time",
        candidates=[{"field": "a", "original": 1, "preferred": 2}],
    )
    assert log_id >= 1
    # 별도 커넥션(load) 으로 재조회 -> 명시 commit 이 보존됐는지 확인.
    row = feedback_db.get_candidate_log(log_id)
    assert row is not None
    assert row["session_id"] == "s1"
    assert row["original"] == {"a": 1}
    assert row["pattern_type"] == "one_time"


def test_save_user_preference_persists():
    feedback_db.save_user_preference(
        field="date", original_pattern="vague", preferred="pending"
    )
    prefs = feedback_db.load_user_preferences()
    assert len(prefs) == 1
    assert prefs[0]["field"] == "date"
    assert prefs[0]["preferred"] == "pending"


def test_save_preference_persists():
    pref_store.save_preference(original={"x": 1}, modified={"x": 2})
    prefs = pref_store.load_preferences()
    assert len(prefs) == 1
    assert prefs[0]["original"] == {"x": 1}
    assert prefs[0]["modified"] == {"x": 2}

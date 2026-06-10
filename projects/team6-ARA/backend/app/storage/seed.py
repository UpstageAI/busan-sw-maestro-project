"""충돌 시연용 기존 데이터 seed.

주의: seed_if_empty() 는 /route 등 일반 요청 경로에서 절대 자동 실행하지 않는다.
("저장 전 사용자 승인" 제약과 구분되는 '시연용 시스템 데이터'다.)
호출 경로는 (a) 테스트 fixture, (b) 명시적 POST /mock/seed 뿐이다.

기준일은 2026-06-05 로 고정해 데모 재현성을 보장한다.
- calendar_events: 다음 주 화요일(2026-06-09) 10:00 기존 회의 -> Tier2 충돌 유발
- tasks: 박성종의 2026-06-06 발표자료 -> Task 중복 유발
"""

from app.storage.db import get_conn

# (title, date, time, all_day, duration_estimate)
_SEED_CALENDAR = [
    ("기존 스프린트 회의", "2026-06-09", "10:00", 0, 60),
]
# (title, assignee, due_date, priority)
_SEED_TASKS = [
    ("발표자료 만들기", "박성종", "2026-06-06", "high"),
]


def seed_if_empty() -> dict[str, int]:
    """저장소가 비어 있을 때만 시연용 데이터를 넣는다 (멱등).

    Returns: 삽입된 행 수 {"calendar_events": n, "tasks": n}.
    """
    inserted = {"calendar_events": 0, "tasks": 0}
    with get_conn() as conn:
        cal_count = conn.execute(
            "SELECT COUNT(*) FROM calendar_events"
        ).fetchone()[0]
        if cal_count == 0:
            conn.executemany(
                "INSERT INTO calendar_events "
                "(title, date, time, all_day, duration_estimate) "
                "VALUES (?, ?, ?, ?, ?)",
                _SEED_CALENDAR,
            )
            inserted["calendar_events"] = len(_SEED_CALENDAR)

        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if task_count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, assignee, due_date, priority) "
                "VALUES (?, ?, ?, ?)",
                _SEED_TASKS,
            )
            inserted["tasks"] = len(_SEED_TASKS)
        conn.commit()
    return inserted

"""규칙 기반 충돌 검사 단위 테스트."""

from app.conflict.rules import check_conflict
from app.schemas.items import Item
from app.schemas.routing import ConflictKind

_EXISTING_CAL = [
    {
        "id": 1,
        "title": "기존 회의",
        "date": "2026-06-09",
        "time": "10:00",
        "all_day": 0,
        "duration_estimate": 60,
    }
]
_EXISTING_TASK = [
    {
        "id": 1,
        "title": "발표자료 만들기",
        "assignee": "박성종",
        "due_date": "2026-06-06",
        "priority": "high",
    }
]


def test_calendar_overlap_detected():
    item = Item(id="a", type="calendar", title="팀 회의", date="2026-06-09", time="10:30")
    r = check_conflict(item, _EXISTING_CAL, [])
    assert r.has_conflict
    assert r.kind == ConflictKind.calendar_overlap
    assert r.suggested_alternatives  # 대체 경로 제안 있음


def test_calendar_no_overlap_different_time():
    item = Item(id="a", type="calendar", title="팀 회의", date="2026-06-09", time="14:00")
    assert not check_conflict(item, _EXISTING_CAL, []).has_conflict


def test_calendar_no_overlap_different_date():
    item = Item(id="a", type="calendar", title="팀 회의", date="2026-06-10", time="10:00")
    assert not check_conflict(item, _EXISTING_CAL, []).has_conflict


def test_calendar_all_day_excluded():
    item = Item(
        id="a", type="calendar", title="종일", date="2026-06-09", time="10:00", all_day=True
    )
    assert not check_conflict(item, _EXISTING_CAL, []).has_conflict


def test_task_duplicate_exact():
    item = Item(
        id="d", type="task", title="발표자료 만들기", assignee="박성종", due_date="2026-06-06"
    )
    r = check_conflict(item, [], _EXISTING_TASK)
    assert r.has_conflict
    assert r.kind == ConflictKind.task_duplicate


def test_task_duplicate_near_due_date():
    # 마감일 +1일 근접도 중복으로 본다
    item = Item(
        id="d", type="task", title="발표자료 만들기", assignee="박성종", due_date="2026-06-07"
    )
    assert check_conflict(item, [], _EXISTING_TASK).has_conflict


def test_task_no_duplicate_different_assignee():
    item = Item(
        id="d", type="task", title="발표자료 만들기", assignee="이동근", due_date="2026-06-06"
    )
    assert not check_conflict(item, [], _EXISTING_TASK).has_conflict


def test_task_no_duplicate_far_due_date():
    item = Item(
        id="d", type="task", title="발표자료 만들기", assignee="박성종", due_date="2026-06-20"
    )
    assert not check_conflict(item, [], _EXISTING_TASK).has_conflict


def test_memo_and_risk_not_checked():
    memo = Item(id="m", type="memo", title="발표자료 만들기")
    risk = Item(id="r", type="risk", title="발표자료 만들기", description="x")
    assert not check_conflict(memo, [], _EXISTING_TASK).has_conflict
    assert not check_conflict(risk, _EXISTING_CAL, _EXISTING_TASK).has_conflict

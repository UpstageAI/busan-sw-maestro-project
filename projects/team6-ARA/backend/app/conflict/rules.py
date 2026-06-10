"""규칙 기반 중복/충돌 검사 (LLM 미사용, MVP).

- Calendar: 같은 일자에서 시간대 겹침 (all_day 제외, 기본 60분)
- Task: 제목 유사(완전일치 또는 토큰 Jaccard>=0.6) + 담당자 동일 + 마감일 +-1일 근접
- Memo / Risk: 검사하지 않음 (항상 충돌 없음)

유사도/일정 판정의 LLM 보조는 모델 미정이라 미구현이다. (# TODO 훅 참조)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.schemas.items import Item, ItemType
from app.schemas.routing import (
    ConflictAlternative,
    ConflictCheckResult,
    ConflictKind,
)

logger = logging.getLogger("agent.conflict")

_DEFAULT_DURATION_MIN = 60  # 시작시간만 있을 때 기본 1시간
_JACCARD_THRESHOLD = 0.6
_DUE_DATE_NEAR_DAYS = 1


def _parse_hhmm(value: str | None) -> int | None:
    """'HH:MM' -> 자정 기준 분. 파싱 실패 시 None."""
    if not value:
        return None
    try:
        t = datetime.strptime(value.strip(), "%H:%M")
    except ValueError:
        return None
    return t.hour * 60 + t.minute


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def _title_tokens(title: str) -> set[str]:
    return set(_normalize_title(title).split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    # datetime 은 date 의 서브클래스라 isinstance(date) 를 통과해버린다.
    # 그대로 두면 date 와 == 비교가 어긋나므로 먼저 .date() 로 떨군다.
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def check_calendar_conflict(
    item: Item, existing: list[dict[str, Any]]
) -> ConflictCheckResult:
    result = ConflictCheckResult(item_id=item.id or "", kind=ConflictKind.none)
    if item.all_day:
        return result  # all_day 일정은 충돌 검사 제외

    new_start = _parse_hhmm(item.time)
    new_date = _parse_date(item.date)
    if new_start is None or new_date is None:
        return result  # 시간/일자 없으면 겹침 판정 불가
    new_dur = item.duration_estimate or _DEFAULT_DURATION_MIN
    new_end = new_start + new_dur
    # 가정: 같은 날짜 안에서만 겹침을 본다(자정 넘김 미처리). 23:00+120분처럼
    # new_end 가 1440 을 넘겨 다음 날로 흘러도 다음 날 일정과는 대조하지 않는다.
    # 데모 일정(60분)에선 발생하지 않는다. 다중일 인터벌은 후순위(review-result.md).

    conflicts: list[dict[str, Any]] = []
    for ev in existing:
        if ev.get("all_day"):
            continue
        if _parse_date(ev.get("date")) != new_date:
            continue
        ev_start = _parse_hhmm(ev.get("time"))
        if ev_start is None:
            continue
        ev_dur = ev.get("duration_estimate") or _DEFAULT_DURATION_MIN
        ev_end = ev_start + ev_dur
        # 범위 겹침: new_start < ev_end AND ev_start < new_end
        if new_start < ev_end and ev_start < new_end:
            conflicts.append(ev)

    if conflicts:
        result.kind = ConflictKind.calendar_overlap
        result.has_conflict = True
        result.conflicting_with = conflicts
        result.warning = (
            f"{new_date} {item.time} 시간대에 기존 일정 {len(conflicts)}건과 겹칩니다."
        )
        result.suggested_alternatives = [
            ConflictAlternative.modify,
            ConflictAlternative.pending,
        ]
        logger.warning(
            "충돌 감지(calendar): item=%s date=%s time=%s conflicts=%d",
            item.id,
            new_date,
            item.time,
            len(conflicts),
        )
    return result


def check_task_duplicate(
    item: Item, existing: list[dict[str, Any]]
) -> ConflictCheckResult:
    result = ConflictCheckResult(item_id=item.id or "", kind=ConflictKind.none)
    new_norm = _normalize_title(item.title)
    new_tokens = _title_tokens(item.title)
    new_due = _parse_date(item.due_date)

    dups: list[dict[str, Any]] = []
    for t in existing:
        existing_title = t.get("title") or ""
        # 1) 제목 유사
        title_match = (
            _normalize_title(existing_title) == new_norm
            or _jaccard(new_tokens, _title_tokens(existing_title))
            >= _JACCARD_THRESHOLD
        )
        if not title_match:
            continue
        # 2) 담당자 동일
        if (t.get("assignee") or None) != (item.assignee or None):
            continue
        # 3) 마감일 동일/근접 (+-1일). 둘 다 없으면 근접으로 간주.
        existing_due = _parse_date(t.get("due_date"))
        if new_due is not None and existing_due is not None:
            if abs((existing_due - new_due).days) > _DUE_DATE_NEAR_DAYS:
                continue
        elif new_due != existing_due:
            # 한쪽만 마감일이 있으면 중복으로 보지 않는다.
            continue
        # TODO: 애매한 제목 유사도는 향후 LLM 보조 판정 (모델 미정)
        dups.append(t)

    if dups:
        result.kind = ConflictKind.task_duplicate
        result.has_conflict = True
        result.conflicting_with = dups
        result.warning = (
            f"제목/담당자/마감이 유사한 기존 작업 {len(dups)}건이 있습니다."
        )
        result.suggested_alternatives = [
            ConflictAlternative.merge,
            ConflictAlternative.modify,
            ConflictAlternative.pending,
        ]
        logger.warning(
            "충돌 감지(task): item=%s title=%s dups=%d",
            item.id,
            item.title,
            len(dups),
        )
    return result


def check_conflict(
    item: Item,
    calendar_events: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> ConflictCheckResult:
    """item type 에 따라 적절한 충돌 검사를 수행한다.

    memo / risk / pending / ignore 는 검사 없이 충돌 없음을 반환한다.
    """
    if item.type == ItemType.calendar:
        return check_calendar_conflict(item, calendar_events)
    if item.type == ItemType.task:
        return check_task_duplicate(item, tasks)
    return ConflictCheckResult(item_id=item.id or "", kind=ConflictKind.none)

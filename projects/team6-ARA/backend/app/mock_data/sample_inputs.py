"""6-2 단독/데모용 6-1 Item 샘플 입력.

기준일 2026-06-05(금) 고정 -> "내일"=06-06, "다음 주 화"=06-09, "다음 주 금"=06-12.
planning.md 필수 시나리오 3종에 대응한다. seed 의 기존 데이터(2026-06-09 10:00 회의,
박성종 06-06 발표자료)와 함께 충돌/중복을 시연한다.
"""

from typing import Any

# 시나리오 1: 다항목 분해 (task x3 + calendar x1)
_SCENARIO_MULTI: dict[str, Any] = {
    "session_id": "demo-multi",
    "items": [
        {
            "id": "m-1",
            "type": "task",
            "title": "발표자료 만들기",
            "assignee": "박성종",
            "due_date": "2026-06-06",
            "priority": "high",
            "confidence": 0.91,
            "source_sentence": "내일까지 성종은 발표자료",
        },
        {
            "id": "m-2",
            "type": "task",
            "title": "API 테스트 정리",
            "assignee": "이동근",
            "due_date": "2026-06-06",
            "priority": "medium",
            "confidence": 0.88,
            "source_sentence": "동근은 API 테스트 정리",
        },
        {
            "id": "m-3",
            "type": "task",
            "title": "데모 영상 준비",
            "assignee": "이우태",
            "due_date": "2026-06-06",
            "priority": "medium",
            "confidence": 0.86,
            "source_sentence": "우태는 데모 영상 준비",
        },
        {
            "id": "m-4",
            "type": "calendar",
            "title": "최종 리허설",
            "date": "2026-06-12",
            "time": "10:00",
            "duration_estimate": 60,
            "confidence": 0.9,
            "source_sentence": "금요일 오전 10시 최종 리허설하자",
        },
    ],
}

# 시나리오 2: 모호 일정 -> Pending + 리스크 분리 (pending x1 + risk x1)
_SCENARIO_VAGUE_RISK: dict[str, Any] = {
    "session_id": "demo-vague-risk",
    "items": [
        {
            "id": "v-1",
            "type": "pending",
            "title": "멘토님께 보여드리기",
            "confidence": 0.45,
            "needs_confirmation": True,
            "clarification_question": "구체적인 날짜가 언제인가요? ('다음 주쯤'은 모호합니다)",
            "source_sentence": "다음 주쯤 멘토님께 보여드리고",
        },
        {
            "id": "v-2",
            "type": "risk",
            "title": "캘린더 연동 리스크",
            "description": "캘린더 연동이 안 될 가능성이 있음",
            "mitigation": "안 되면 캘린더 연동은 Mock 으로 대체",
            "confidence": 0.8,
            "source_sentence": "안 되면 캘린더 연동은 Mock으로 대체하자",
        },
    ],
}

# 시나리오 3: 일정 충돌 (calendar x1, seed 의 06-09 10:00 회의와 충돌)
_SCENARIO_CONFLICT: dict[str, Any] = {
    "session_id": "demo-conflict",
    "items": [
        {
            "id": "c-1",
            "type": "calendar",
            "title": "팀 회의",
            "date": "2026-06-09",
            "time": "10:00",
            "duration_estimate": 60,
            "confidence": 0.92,
            "source_sentence": "다음 주 화요일 오전 10시에 팀 회의 잡자",
        },
    ],
}

SAMPLE_SCENARIOS: dict[str, dict[str, Any]] = {
    "multi": _SCENARIO_MULTI,
    "vague_risk": _SCENARIO_VAGUE_RISK,
    "conflict": _SCENARIO_CONFLICT,
}


def get_scenario(name: str) -> dict[str, Any]:
    """이름으로 시나리오 입력을 돌려준다. 없으면 KeyError."""
    return SAMPLE_SCENARIOS[name]

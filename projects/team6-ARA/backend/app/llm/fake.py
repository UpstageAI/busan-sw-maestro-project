"""오프라인/테스트용 고정 LLM.

planning.md 필수 시나리오를 키워드로 식별해 결정적 JSON을 돌려준다.
데모 안정성 + 회귀 테스트 픽스처 역할을 겸한다. 그 외 입력은 best-effort 단일 메모.
입력 유형 라벨은 두지 않는다(실행 항목 없으면 items=[]).
"""

from app.schemas.analysis import ContextBundle
from app.logging_config import get_logger

logger = get_logger("llm.fake")


class FakeLLM:
    def analyze(self, *, raw_text: str, base_date: str, context: ContextBundle) -> dict:
        if "리허설" in raw_text:
            logger.info("FakeLLM scenario selected: multi_items")
            return _SCENARIO_1
        if "멘토님" in raw_text:
            logger.info("FakeLLM scenario selected: vague_risk")
            return _SCENARIO_2
        if "회의" in raw_text:
            logger.info("FakeLLM scenario selected: conflict")
            return _SCENARIO_3
        logger.info("FakeLLM scenario selected: fallback_memo")
        return {
            "items": [{
                "type": "memo", "title": raw_text[:30] or "메모",
                "source_sentence": raw_text, "recommended_tool": "create_memo",
                "type_certainty": 0.8, "date_status": "missing", "required_ok": True,
            }],
        }


# 시나리오 1: 다항목 분해 (task×3 + calendar×1), 전부 명확 → 확인 불필요
_SCENARIO_1 = {
    "items": [
        {"type": "task", "title": "발표자료 만들기", "assignee": "박성종",
         "date": "2026-06-06", "priority": "high", "source_sentence": "내일까지 성종은 발표자료",
         "recommended_tool": "create_task", "type_certainty": 0.92, "date_status": "concrete",
         "assignee_present": True, "required_ok": True},
        {"type": "task", "title": "API 테스트 정리", "assignee": "이동근",
         "date": "2026-06-06", "priority": "high", "source_sentence": "동근은 API 테스트 정리",
         "recommended_tool": "create_task", "type_certainty": 0.9, "date_status": "concrete",
         "assignee_present": True, "required_ok": True},
        {"type": "task", "title": "데모 영상 준비", "assignee": "이우태",
         "date": "2026-06-06", "priority": "high", "source_sentence": "우태는 데모 영상 준비",
         "recommended_tool": "create_task", "type_certainty": 0.9, "date_status": "concrete",
         "assignee_present": True, "required_ok": True},
        {"type": "calendar", "title": "최종 리허설", "date": "2026-06-12", "time": "10:00",
         "priority": "medium", "source_sentence": "금요일 오전 10시 최종 리허설",
         "recommended_tool": "create_calendar_event", "type_certainty": 0.93,
         "date_status": "concrete", "time_present": True, "required_ok": True},
    ],
}

# 시나리오 2: 모호 일정 → 정보 부족(확인 필요) + 리스크(mitigation)
_SCENARIO_2 = {
    "items": [
        {"type": "calendar", "title": "멘토님께 보여드리기", "date": None, "time": None,
         "priority": "medium", "source_sentence": "다음 주쯤 멘토님께 보여드리고",
         "recommended_tool": "create_calendar_event", "type_certainty": 0.85,
         "date_status": "vague", "time_present": False, "required_ok": True},
        {"type": "risk", "title": "캘린더 연동 실패 시 Mock 대체",
         "priority": "medium", "source_sentence": "안 되면 캘린더 연동은 Mock으로 대체하자",
         "recommended_tool": "create_risk_log", "type_certainty": 0.8,
         "date_status": "missing", "required_ok": True},
    ],
}

# 시나리오 3: 명확한 단일 일정 (6-2에서 기존 일정과 충돌 검증)
_SCENARIO_3 = {
    "items": [
        {"type": "calendar", "title": "팀 회의", "date": "2026-06-09", "time": "10:00",
         "priority": "medium", "source_sentence": "다음 주 화요일 오전 10시에 팀 회의 잡자",
         "recommended_tool": "create_calendar_event", "type_certainty": 0.95,
         "date_status": "concrete", "time_present": True, "required_ok": True},
    ],
}

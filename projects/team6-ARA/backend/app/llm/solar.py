"""Upstage Solar 클라이언트.

사용 전 준비:
    export UPSTAGE_API_KEY=...        # Upstage 콘솔 발급
    export SOLAR_MODEL=solar-pro      # (선택) 기본값 solar-pro

planning.md: Solar의 JSON 출력을 코드가 해석한다 → 여기선 raw JSON만 받고,
검증/재시도는 pipeline이 담당한다. langchain_upstage import는 지연(lazy)해서
키가 없을 때(FakeLLM 경로)는 이 모듈이 의존성을 요구하지 않게 한다.
"""

import json
import os
from datetime import date

from app.logging_config import compact_text, get_logger, log_payloads_enabled
from app.schemas.analysis import ContextBundle

logger = get_logger("llm.solar")

# reasoning_effort 파라미터를 지원하는 모델(화이트리스트). 그 외 모델에 보내면 422.
_REASONING_EFFORT_MODELS = {"solar-pro2", "solar-pro3"}

_SYSTEM = """너는 비정형 텍스트에서 실행 항목을 뽑아 분류하는 분석기다.
반드시 아래 JSON 스키마만 출력한다(설명/마크다운 금지).

{
  "items": [{
    "type": "task|calendar|memo|risk",
    "title": "string",
    "assignee": "string|null",
    "date": "YYYY-MM-DD|null",
    "time": "HH:MM|null",
    "priority": "high|medium|low",
    "mitigation": "string|null",
    "source_sentence": "근거 원문",
    "recommended_tool": "create_task|create_calendar_event|create_memo|create_risk_log",
    "type_certainty": 0.0-1.0,
    "date_status": "concrete|vague|missing",
    "assignee_present": true/false,
    "time_present": true/false,
    "needs_base_event": true/false,
    "required_ok": true/false
  }]
}

규칙:
- 점수(confidence)는 매기지 마라. 위 플래그만 정확히 채운다.
- 유형은 task/calendar/memo/risk 4종만 쓴다(보류·무시 같은 유형은 만들지 마라).
  확신이 낮으면 그래도 가장 그럴듯한 type을 고르고 type_certainty를 낮게 준다.
- 특정 시각이 있으면 calendar, 산출물+마감이면 task.
- 상대 날짜는 기준 날짜(KST)로 환산한다.
- 기준 날짜의 요일을 반드시 사용한다. "다음 주 화요일"은 기준 날짜가 속한 주의
  다음 주 화요일이다. 임의로 한 주를 더 밀지 마라.
- "내일", "내일까지"는 기준 날짜 + 1일이다.
- "다음 주쯤", "언젠가", "~전까지"처럼 모호한 날짜/기준 이벤트 표현은
  date_status="vague" 또는 needs_base_event=true로 두고 정확한 날짜를 지어내지 마라.
- "안 되면", "실패하면", "대체", "Mock"처럼 실패 조건과 대응 방안이 함께 나오면
  task가 아니라 risk로 분류하고 recommended_tool="create_risk_log"를 사용한다.
  대응 방안을 별도 task로 만들지 말고 그 risk 항목의 mitigation 에 넣는다.
  대응 방안이 없으면 mitigation=null. (risk 외 유형은 mitigation=null)
- 한 입력에 여러 항목이 섞이면 독립 항목으로 분해한다.
- User Preference 가 주어지면, 같은 field 에서 입력이 그 original_pattern 에 해당하는
  상황일 때 사용자가 과거에 선택한 preferred 값을 기본값으로 반영한다.
  단, 입력에 명시적으로 다른 값이 있으면 입력을 우선한다.
- Guideline 이 주어지면 분석/분류 시 그 지침을 따른다(입력과 충돌하면 입력을 우선한다).
- 실행 항목이 전혀 없으면 items=[] (빈 배열)."""


class SolarLLM:
    def __init__(self) -> None:
        from langchain_upstage import ChatUpstage  # lazy

        self._model = os.getenv("SOLAR_MODEL", "solar-pro")
        effort = os.getenv("SOLAR_REASONING_EFFORT")  # "high"|"medium"|"low"|None
        logger.info("SolarLLM init: model=%s reasoning_effort=%s", self._model, effort)
        kwargs: dict = {"model": self._model}
        # reasoning_effort 는 reasoning 지원 모델만 받는다(미지원 모델에 보내면 422).
        if effort and self._model in _REASONING_EFFORT_MODELS:
            kwargs["reasoning_effort"] = effort
        self._llm = ChatUpstage(**kwargs)

    def analyze(self, *, raw_text: str, base_date: str, context: ContextBundle) -> dict:
        logger.info(
            "Solar analyze start: model=%s base_date=%s raw_len=%d prefs=%d guidelines=%d",
            self._model,
            base_date,
            len(raw_text),
            len(context.preferences),
            len(context.guidelines),
        )
        if log_payloads_enabled():
            logger.debug("Solar analyze raw_text=%s", compact_text(raw_text, limit=800))
        human = (
            f"기준 날짜(KST): {_format_base_date(base_date)}\n"
            f"User Preference: {json.dumps(context.preferences, ensure_ascii=False)}\n"
            f"Guideline: {json.dumps(context.guidelines, ensure_ascii=False)}\n"
            f"기존 항목 요약: {context.existing_items_summary}\n\n"
            f"입력:\n{raw_text}"
        )
        resp = self._llm.invoke([("system", _SYSTEM), ("human", human)])
        logger.info("Solar analyze response received: chars=%d", len(resp.content or ""))
        if log_payloads_enabled():
            logger.debug("Solar raw response=%s", compact_text(resp.content, limit=1200))
        return _extract_json(resp.content)


def _format_base_date(base_date: str) -> str:
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    try:
        parsed = date.fromisoformat(base_date)
    except ValueError:
        return base_date
    return f"{base_date} ({weekdays[parsed.weekday()]})"


def _extract_json(content: str) -> dict:
    """코드펜스가 끼어도 본문 JSON만 떼어낸다. 파싱 실패는 pipeline이 재시도로 처리."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        text = text[4:] if text.lower().startswith("json") else text
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or start > end:
        raise ValueError("Solar response does not contain a JSON object")
    parsed = json.loads(text[start : end + 1])
    logger.debug(
        "Solar JSON extracted: top_keys=%s item_count=%d",
        sorted(parsed.keys()),
        len(parsed.get("items", [])) if isinstance(parsed, dict) else -1,
    )
    return parsed

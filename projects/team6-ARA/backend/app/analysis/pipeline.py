"""6-1 파이프라인 오케스트레이션.

Context Loader → (1 LLM 호출) → Pydantic 검증(1회 재시도) → 선호 2차(stub) → Completeness.
planning.md: 검증 실패 시 1회 재시도, 그래도 실패하면 분석 실패 + 원문을 Pending으로.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from pydantic import ValidationError

from app.analysis.completeness import finalize
from app.feedback.db import load_user_preferences
from app.llm.base import LLMClient, get_llm
from app.storage.queries import load_calendar_events, load_tasks
from app.logging_config import (
    compact_text,
    get_logger,
    log_payloads_enabled,
    summarize_items,
)
from app.schemas.analysis import AnalyzeResult, ContextBundle, Item, LLMOutput
from app.schemas.items import ItemType, ToolName

logger = get_logger("analysis.pipeline")

# 분석 지침(D4). Store 풀구축 대신 JSON 파일로 주입한다(없으면 빈 지침).
_GUIDELINES_PATH = Path(__file__).parent.parent.parent / "guidelines.json"

_KOREAN_WEEKDAYS = {
    "월요일": 0, "월": 0,
    "화요일": 1, "화": 1,
    "수요일": 2, "수": 2,
    "목요일": 3, "목": 3,
    "금요일": 4, "금": 4,
    "토요일": 5, "토": 5,
    "일요일": 6, "일": 6,
}


def _summarize_existing(limit: int = 10) -> str:
    """저장소의 기존 일정/할일을 LLM 프롬프트용 요약 문자열로 만든다.

    LLM이 "이미 비슷한 일정/할일이 있다"를 알고 중복 생성을 피하거나 맥락에 맞게 분류하도록
    돕는다. 조회 실패(미초기화 DB 등)는 빈 문자열로 폴백해 분석을 막지 않는다.
    """
    try:
        events = load_calendar_events()
        tasks = load_tasks()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Existing-items load failed, skip summary: %s: %s", exc.__class__.__name__, exc
        )
        return ""
    parts: list[str] = []
    if events:
        ev = "; ".join(
            f"{e.get('date') or '날짜미정'} {e.get('time') or ''} {e.get('title', '')}".strip()
            for e in events[:limit]
        )
        parts.append(f"기존 일정: {ev}")
    if tasks:
        tk = "; ".join(
            f"{t.get('title', '')}(담당 {t.get('assignee') or '미정'}, 마감 {t.get('due_date') or '미정'})"
            for t in tasks[:limit]
        )
        parts.append(f"기존 할일: {tk}")
    return " / ".join(parts)


def _load_guidelines() -> list[dict]:
    """guidelines.json(있으면)을 읽어 분석 지침(D4)으로 주입한다.

    파일이 없거나 깨졌으면 빈 지침으로 폴백한다(분석을 막지 않음). JSON 최상위는 dict 배열.
    """
    try:
        with open(_GUIDELINES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Guidelines load failed, skip: %s: %s", exc.__class__.__name__, exc)
        return []
    if not isinstance(data, list):
        logger.warning("Guidelines must be a JSON array, got %s", type(data).__name__)
        return []
    return [d for d in data if isinstance(d, dict)]


def load_context() -> ContextBundle:
    """Context Loader.

    6-3의 feedback.db `load_user_preferences()`로 저장된 선호를 재주입하고(D3),
    저장소의 기존 항목 요약과 분석 지침(D4, guidelines.json)을 붙인다.
    각 로드가 실패해도 분석 자체는 막지 않는다(빈 값 폴백).
    """
    try:
        preferences = load_user_preferences()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Preference load failed, fallback to empty: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        preferences = []
    existing_summary = _summarize_existing()
    guidelines = _load_guidelines()
    context = ContextBundle(
        preferences=preferences,
        guidelines=guidelines,
        existing_items_summary=existing_summary,
    )
    if preferences:
        logger.info("Context loaded: re-injecting %d saved preference(s)", len(preferences))
    if guidelines:
        logger.info("Context loaded: %d guideline(s)", len(guidelines))
    if existing_summary:
        logger.info("Context loaded: existing-items summary len=%d", len(existing_summary))
    logger.debug(
        "Context loaded: prefs=%d guidelines=%d existing_summary_len=%d",
        len(context.preferences),
        len(context.guidelines),
        len(context.existing_items_summary),
    )
    return context


def _postprocess(result: AnalyzeResult, context: ContextBundle) -> AnalyzeResult:
    """선호 2차 재보정.

    선호를 프롬프트로 LLM에 알려주는 것(D3)과 별개로, LLM 출력 결과를 코드가 한 번 더 검사해
    선호대로 강제 치환한다(LLM은 확률적이라 프롬프트 지시를 가끔 무시 -> 결정적 보장).
    필드값은 직렬화(mode=json) 기준으로 비교/치환하고, 치환 후 재검증으로 타입을 강제한다.
    """
    prefs = context.preferences
    if not prefs:
        logger.debug(
            "Postprocess pass-through (no prefs): %s",
            summarize_items([item.model_dump() for item in result.items]),
        )
        return result

    items: list[Item] = []
    changed = 0
    for item in result.items:
        dump = item.model_dump(mode="json")
        applied = False
        for pref in prefs:
            field = pref.get("field")
            if field in dump and dump[field] == pref.get("original_pattern"):
                dump[field] = pref.get("preferred")
                applied = True
        if applied:
            # 재검증으로 타입(date/enum) 강제. 선호 보정은 best-effort 라, preferred 값이
            # 해당 필드에 invalid 하면(예: date 필드에 비날짜) 원본 항목을 유지하고 분석을
            # 계속한다(보정 실패가 정상 LLM 결과를 분석 실패로 뒤집지 않게).
            try:
                items.append(Item.model_validate(dump))
                changed += 1
            except ValidationError as exc:
                logger.warning(
                    "Postprocess skip (invalid preference value): item=%s: %s",
                    item.title,
                    compact_text(str(exc), limit=200),
                )
                items.append(item)
        else:
            items.append(item)

    if changed:
        logger.info("Postprocess: %d item(s) corrected by preference", changed)
    logger.debug(
        "Postprocess done: changed=%d prefs=%d guidelines=%d",
        changed,
        len(prefs),
        len(context.guidelines),
    )
    return AnalyzeResult(items=items)


def analyze(*, raw_text: str, base_date: str, llm: LLMClient | None = None) -> AnalyzeResult:
    llm = llm or get_llm()
    logger.info(
        "Analyze pipeline start: base_date=%s raw_len=%d llm=%s",
        base_date,
        len(raw_text),
        llm.__class__.__name__,
    )
    if log_payloads_enabled():
        logger.debug("Analyze raw_text=%s", compact_text(raw_text, limit=800))
    context = load_context()

    output = _call_with_retry(llm, raw_text, base_date, context)
    if output is None:
        logger.error("Analyze pipeline failed after retries: raw_len=%d", len(raw_text))
        return _analysis_failed(raw_text)

    output = _normalize_relative_dates(output, base_date)
    result = finalize(output)
    result = _postprocess(result, context)
    logger.info("Analyze pipeline complete: %s", summarize_items([it.model_dump() for it in result.items]))
    return result


def _call_with_retry(
    llm: LLMClient, raw_text: str, base_date: str, context: ContextBundle, attempts: int = 2
) -> LLMOutput | None:
    for attempt in range(1, attempts + 1):
        try:
            logger.info("LLM attempt %d/%d start", attempt, attempts)
            raw = llm.analyze(raw_text=raw_text, base_date=base_date, context=context)
            output = LLMOutput.model_validate(raw)
            logger.info("LLM attempt %d/%d validated: %s", attempt, attempts, summarize_items(output.items))
            return output
        except Exception as exc:  # noqa: BLE001
            # 검증 실패(ValidationError/ValueError/KeyError)뿐 아니라 네트워크/Solar API
            # 오류(httpx/upstage 등)도 잡아 재시도하고, 끝내 실패하면 None 을 돌려
            # 호출부가 _analysis_failed(Pending 저장)로 폴백하게 한다(500 방지).
            logger.warning(
                "LLM attempt %d/%d failed: %s: %s",
                attempt,
                attempts,
                exc.__class__.__name__,
                compact_text(str(exc), limit=240),
            )
            continue
    return None


def _analysis_failed(raw_text: str) -> AnalyzeResult:
    """분석 실패 → 원문을 미분류 보류 항목으로 (확인 필요)."""
    logger.warning("Analyze fallback to pending item: raw_len=%d", len(raw_text))
    return AnalyzeResult(
        items=[Item(
            type=ItemType.pending,
            title="분석 실패",
            source_sentence=raw_text,
            recommended_tool=ToolName.save_to_pending,
            confidence=0.0,
            needs_confirmation=True,
            clarification_question="자동 분석에 실패했습니다. 원문을 직접 확인해 주세요.",
        )],
    )


def _normalize_relative_dates(output: LLMOutput, base_date: str) -> LLMOutput:
    """LLM이 흔들리기 쉬운 명확한 상대 날짜만 코드에서 보정한다."""
    try:
        base = date.fromisoformat(base_date)
    except ValueError:
        logger.warning("Date normalization skipped: invalid base_date=%s", base_date)
        return output

    normalized = []
    changed = 0
    for item in output.items:
        sentence = item.source_sentence
        updates: dict[str, object] = {}

        next_weekday = _next_weekday(sentence, base)
        if next_weekday is not None:
            updates.update(date=next_weekday.isoformat(), date_status="concrete")
        elif "내일까지" in sentence or "내일" in sentence:
            updates.update(date=(base + timedelta(days=1)).isoformat(), date_status="concrete")

        if "쯤" in sentence:
            updates.update(date=None, date_status="vague")

        if updates:
            changed += 1
            logger.debug(
                "Date normalized: title=%s updates=%s source=%s",
                item.title,
                updates,
                compact_text(sentence),
            )
        normalized.append(item.model_copy(update=updates) if updates else item)

    logger.info("Date normalization complete: changed=%d total=%d", changed, len(output.items))
    return LLMOutput(items=normalized)


def _next_weekday(sentence: str, base: date) -> date | None:
    if "다음 주" not in sentence and "다음주" not in sentence:
        return None

    for label, target_weekday in _KOREAN_WEEKDAYS.items():
        if label in sentence:
            start_of_week = base - timedelta(days=base.weekday())
            return start_of_week + timedelta(days=7 + target_weekday)
    return None

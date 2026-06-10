"""6-1 파이프라인 오케스트레이션.

Context Loader → (1 LLM 호출) → Pydantic 검증(1회 재시도) → 선호 2차(stub) → Completeness.
planning.md: 검증 실패 시 1회 재시도, 그래도 실패하면 분석 실패 + 원문을 Pending으로.
"""

from datetime import date, timedelta

from pydantic import ValidationError

from app.analysis.completeness import finalize
from app.llm.base import LLMClient, get_llm
from app.logging_config import (
    compact_text,
    get_logger,
    log_payloads_enabled,
    summarize_items,
)
from app.schemas.analysis import AnalyzeResult, ContextBundle, Item, LLMOutput
from app.schemas.items import ItemType, ToolName

logger = get_logger("analysis.pipeline")

_KOREAN_WEEKDAYS = {
    "월요일": 0, "월": 0,
    "화요일": 1, "화": 1,
    "수요일": 2, "수": 2,
    "목요일": 3, "목": 3,
    "금요일": 4, "금": 4,
    "토요일": 5, "토": 5,
    "일요일": 6, "일": 6,
}


def load_context() -> ContextBundle:
    """Context Loader (M1 stub).

    M3에서 6-3의 feedback.db `load_user_preferences()`를 재사용해 선호를 채우고(D3),
    Guideline Store(D4)·기존 항목 요약을 붙인다. 지금은 빈 컨텍스트.
    """
    context = ContextBundle()
    logger.debug(
        "Context loaded: prefs=%d guidelines=%d existing_summary_len=%d",
        len(context.preferences),
        len(context.guidelines),
        len(context.existing_items_summary),
    )
    return context


def _postprocess(result: AnalyzeResult, context: ContextBundle) -> AnalyzeResult:
    """선호·지침 2차 재보정 (M3에서 구현). 지금은 통과."""
    logger.debug(
        "Postprocess pass-through: %s prefs=%d guidelines=%d",
        summarize_items([item.model_dump() for item in result.items]),
        len(context.preferences),
        len(context.guidelines),
    )
    return result


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
        except (ValidationError, ValueError, KeyError) as exc:
            logger.warning(
                "LLM attempt %d/%d failed validation: %s: %s",
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

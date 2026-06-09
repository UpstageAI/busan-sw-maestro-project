"""POST /analyze — 6-1 분석 단계 엔드포인트 (FE/6-2 핸드오프).

User Approval 직전까지(= 6-1 산출 items)만 반환한다. 라우팅·승인은 6-2.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.analysis.pipeline import analyze
from app.logging_config import compact_text, get_logger, log_payloads_enabled, summarize_items
from app.schemas.analysis import AnalyzeResult

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger("api.analyze")

_KST = timezone(timedelta(hours=9))


class AnalyzeRequest(BaseModel):
    raw_text: str
    base_date: str | None = None   # "YYYY-MM-DD" (KST). 없으면 오늘.


@router.post("/", response_model=AnalyzeResult)
async def analyze_route(body: AnalyzeRequest) -> AnalyzeResult:
    base_date = body.base_date or datetime.now(_KST).strftime("%Y-%m-%d")
    logger.info(
        "POST /analyze start: base_date=%s raw_len=%d",
        base_date,
        len(body.raw_text),
    )
    if log_payloads_enabled():
        logger.debug("POST /analyze raw_text=%s", compact_text(body.raw_text, limit=800))
    try:
        result = analyze(raw_text=body.raw_text, base_date=base_date)
    except Exception:
        logger.exception("POST /analyze failed: base_date=%s raw_len=%d", base_date, len(body.raw_text))
        raise
    logger.info(
        "POST /analyze complete: %s",
        summarize_items([item.model_dump() for item in result.items]),
    )
    return result

"""LLM seam (D2).

6-1은 LLM을 직접 부르지 않고 이 인터페이스로만 부른다.
- UPSTAGE_API_KEY 있으면 Solar 사용(기본).
- 없으면 FakeLLM로 폴백 → 오프라인/미설정에서도 /analyze·테스트가 돈다.
- LLM_PROVIDER=fake|solar 로 강제 지정 가능.
"""

import os
from typing import Protocol

from app.logging_config import get_logger
from app.schemas.analysis import ContextBundle

logger = get_logger("llm")


class LLMClient(Protocol):
    def analyze(self, *, raw_text: str, base_date: str, context: ContextBundle) -> dict:
        """{"items": [...]} 형태의 raw dict 반환. 검증은 pipeline이 한다."""
        ...


def get_llm() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider == "solar" or (not provider and os.getenv("UPSTAGE_API_KEY")):
        logger.info(
            "LLM provider selected: solar (explicit=%s key_present=%s)",
            bool(provider),
            bool(os.getenv("UPSTAGE_API_KEY")),
        )
        from app.llm.solar import SolarLLM
        return SolarLLM()
    logger.info(
        "LLM provider selected: fake (explicit=%s key_present=%s)",
        provider or "auto",
        bool(os.getenv("UPSTAGE_API_KEY")),
    )
    from app.llm.fake import FakeLLM
    return FakeLLM()

"""Agent 분기/단계 로깅 설정 (시연 영상용).

레벨 사용 기준 (개인 작업 지침):
- DEBUG:   노드 내부 상세
- INFO:    분기/단계 전환
- WARNING: confidence 낮음, Pending 처리, 충돌 감지
- ERROR:   Tool 실패

`agent` 네임스페이스 하위 로거(agent.node.*, agent.conflict 등)를 사용한다.
"""

import logging
import os
from collections import Counter
from typing import Any

_CONFIGURED = False
_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: int | str | None = None) -> logging.Logger:
    """agent 로거를 1회 설정하고 돌려준다 (멱등).

    레벨은 인자 > 환경변수 ACTION_ROUTER_LOG_LEVEL > INFO 순으로 결정.
    """
    global _CONFIGURED
    agent_logger = logging.getLogger("agent")

    if level is None:
        level = os.environ.get("ACTION_ROUTER_LOG_LEVEL", "INFO")
    # 표준 레벨명은 대문자만 유효하다. env/인자로 'debug' 같은 소문자가 와도
    # setLevel 이 ValueError 로 부팅을 깨뜨리지 않도록 정규화한다.
    if isinstance(level, str):
        level = level.upper()
    agent_logger.setLevel(level)

    if not _CONFIGURED:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        agent_logger.addHandler(handler)
        agent_logger.propagate = False
        _CONFIGURED = True

    return agent_logger


def get_logger(name: str) -> logging.Logger:
    """`agent.<name>` 로거를 돌려준다."""
    return logging.getLogger(f"agent.{name}")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def log_payloads_enabled() -> bool:
    """원문/LLM raw payload 같은 상세 데이터 로깅 여부."""
    return env_flag("ACTION_ROUTER_LOG_PAYLOADS")


def compact_text(value: str | None, limit: int = 160) -> str:
    """로그 한 줄에 들어가도록 공백/길이를 정리한다."""
    if not value:
        return ""
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def summarize_items(items: list[Any]) -> str:
    """Item/LLMItem/dict 목록을 type별 카운트 문자열로 요약한다."""
    counter: Counter[str] = Counter()
    for item in items:
        if isinstance(item, dict):
            item_type = item.get("type")
        else:
            item_type = getattr(item, "type", None)
        counter[str(item_type or "unknown")] += 1
    if not counter:
        return "total=0"
    parts = [f"{key}={value}" for key, value in sorted(counter.items())]
    return f"total={len(items)} " + " ".join(parts)

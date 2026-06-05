from __future__ import annotations

import json
import re

from ..llm import chat
from ..prompts import ROUTER_PROMPT
from ..state import AgentState, INTENT_VALUES


_GENERAL_PATTERNS = (
    r"^(안녕|안녕하세요|하이|hello|hi)\b",
    r"^(고마워|감사|땡큐|thanks)\b",
    r"^(너는 누구|뭐 할 수 있어|도움말|help)\??$",
)

_SOMA_KEYWORDS = (
    "소마",
    "sw마에스트로",
    "sw 마에스트로",
    "소프트웨어 마에스트로",
    "부산센터",
    "연수생",
    "멘토",
    "멘토링",
    "엑스퍼트",
    "사무국",
    "예비과정",
    "본과정",
    "교육",
    "특강",
    "심의",
    "프로젝트",
    "팀 구성",
    "제출",
    "서류",
    "출결",
    "출석",
    "결석",
    "지각",
    "개발공간",
    "webex",
    "오리엔테이션",
    "ot",
)

_SCHEDULE_KEYWORDS = (
    "일정",
    "날짜",
    "마감",
    "언제",
    "몇 시",
    "몇시",
    "기한",
    "링크",
    "url",
    "제출일",
)

_SUMMARY_KEYWORDS = (
    "요약",
    "정리",
    "핵심",
    "한줄",
    "한 줄",
    "간단히",
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _rule_based_intent(question: str) -> str | None:
    """명확한 케이스는 규칙으로 먼저 분류해 LLM 오분류를 줄인다."""
    text = _normalize(question)
    if not text:
        return "general"

    if any(re.search(pattern, text) for pattern in _GENERAL_PATTERNS):
        return "general"

    is_soma_domain = _contains_any(text, _SOMA_KEYWORDS)
    if not is_soma_domain:
        return None

    if _contains_any(text, _SUMMARY_KEYWORDS):
        return "soma_summarize"
    if _contains_any(text, _SCHEDULE_KEYWORDS):
        return "schedule_link"
    return "soma_query"


def _fallback_intent(question: str) -> str:
    intent = _rule_based_intent(question)
    if intent:
        return intent

    text = _normalize(question)
    if any(re.search(pattern, text) for pattern in _GENERAL_PATTERNS):
        return "general"
    return "soma_unrelated"


def router_node(state: AgentState) -> dict:
    rule_intent = _rule_based_intent(state["question"])
    if rule_intent:
        return {"intent": rule_intent, "execution_history": ["router"]}

    messages = [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": state["question"]},
    ]
    raw = chat(messages, temperature=0, json_mode=True)
    try:
        intent = json.loads(raw).get("intent", "")
        if intent not in INTENT_VALUES:
            intent = _fallback_intent(state["question"])
    except Exception:
        intent = _fallback_intent(state["question"])

    return {"intent": intent, "execution_history": ["router"]}

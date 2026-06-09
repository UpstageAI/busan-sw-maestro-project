from __future__ import annotations

import operator
from typing import Annotated, TypedDict

# intent 값 목록
# general        : 일반 대화·잡담
# soma_unrelated : 소마 무관 질문
# soma_query     : 소마 관련 정보 질의
# soma_summarize : 소마 자료 요약 요청
# schedule_link  : 일정·링크·마감일 추출 요청
INTENT_VALUES = ("general", "soma_unrelated", "soma_query", "soma_summarize", "schedule_link")


class AgentState(TypedDict):
    question: str
    intent: str
    retrieved_chunks: list[dict]          # [{"content": str, "source": str, "score": float}]
    generated_answer: str
    execution_history: Annotated[list[str], operator.add]  # 각 노드가 이름을 append
    chat_history: list[dict]              # [{"role": "user"|"assistant", "content": str}]

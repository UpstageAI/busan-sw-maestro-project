from __future__ import annotations

from ..state import AgentState

_MSG = (
    "관련 정보를 찾을 수 없어요. "
    "정확한 정보는 SW마에스트로 공식 계정이나 공지사항을 확인해 주세요."
)


def handle_not_found_node(state: AgentState) -> dict:
    return {"generated_answer": _MSG, "execution_history": ["handle_not_found"]}

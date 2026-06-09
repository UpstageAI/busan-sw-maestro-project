from __future__ import annotations

from ..state import AgentState

_MSG = (
    "저는 SW마에스트로 부산센터 자료를 기준으로 답변하는 챗봇이라, "
    "소마와 관련 없는 질문에는 답변하기 어려워요.\n\n"
    "예를 들어 제출 서류, 출결, 멘토링, 교육 일정, 개발공간, Webex 같은 내용을 물어봐 주세요."
)


def handle_irrelevant_node(state: AgentState) -> dict:
    return {"generated_answer": _MSG, "execution_history": ["handle_irrelevant"]}

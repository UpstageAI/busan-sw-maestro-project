from __future__ import annotations

from ..llm import chat
from ..prompts import SYSTEM_PROMPT
from ..state import AgentState
from ...config import get_settings


def handle_general_node(state: AgentState) -> dict:
    s = get_settings()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(state["chat_history"][-s.max_history_turns :])
    messages.append({"role": "user", "content": state["question"]})

    answer = chat(messages, temperature=0.5)
    return {"generated_answer": answer, "execution_history": ["handle_general"]}

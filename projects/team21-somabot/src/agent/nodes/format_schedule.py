from __future__ import annotations

from ..llm import chat
from ..prompts import SYSTEM_PROMPT, SCHEDULE_PROMPT
from ..state import AgentState
from ...config import get_settings


def format_schedule_node(state: AgentState) -> dict:
    s = get_settings()
    context = "\n\n---\n\n".join(
        f"[출처: {c['source']}]\n{c['content']}" for c in state["retrieved_chunks"]
    )
    system = SYSTEM_PROMPT + "\n\n" + SCHEDULE_PROMPT.format(context=context)

    messages = [{"role": "system", "content": system}]
    messages.extend(state["chat_history"][-s.max_history_turns :])
    messages.append({"role": "user", "content": state["question"]})

    answer = chat(messages, temperature=0.1)
    return {"generated_answer": answer, "execution_history": ["format_schedule_link"]}

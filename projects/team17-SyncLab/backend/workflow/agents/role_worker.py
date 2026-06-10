import os
from workflow.state import WorkerState
from workflow.utils import call_llm_with_json_retry
from workflow.llm import get_llm

def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "../../prompts/role_worker.txt")
    with open(os.path.normpath(path), "r", encoding="utf-8") as f:
        return f.read()

def role_worker_node(state: WorkerState) -> dict:
    print(f"[3/6] role_worker 실행 중... (직군: {state['role']})")
    words_list = "\n".join(
        f"- {w['word']} (문맥: {w['context_snippet']})"
        for w in state["extracted_words"]
    )
    prompt = _load_prompt().format(
        role=state["role"],
        input_text=state["input_text"],
        sender_role=state["sender_role"],
        receiver_role=", ".join(state["receiver_roles"]),
        words_list=words_list,
    )
    result = call_llm_with_json_retry(get_llm(), prompt)
    print(f"[3/6] role_worker 완료 (직군: {state['role']})")
    return {"role_interpretations": [result]}

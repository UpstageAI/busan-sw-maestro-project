import os
from workflow.state import GraphState
from workflow.utils import call_llm_with_json_retry
from workflow.llm import get_llm

def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "../../prompts/context_intake.txt")
    with open(os.path.normpath(path), "r", encoding="utf-8") as f:
        return f.read()

def context_intake_node(state: GraphState) -> dict:
    print("[1/5] context_intake 실행 중...")
    prompt = _load_prompt().format(
        sender_role=state["sender_role"],
        receiver_role=", ".join(state["receiver_roles"]),
        communication_type=state["communication_type"],
        input_text=state["input_text"],
    )
    result = call_llm_with_json_retry(get_llm(), prompt)
    print("[1/5] context_intake 완료")
    return {
        "context_analysis": result,
        "summary": result["summary"],
        "key_request": result["keyRequest"],
    }

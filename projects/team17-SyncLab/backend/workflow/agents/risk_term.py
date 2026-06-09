import json
import os
from workflow.state import GraphState
from workflow.utils import call_llm_with_json_retry
from workflow.llm import get_llm

def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "../../prompts/risk_term.txt")
    with open(os.path.normpath(path), "r", encoding="utf-8") as f:
        return f.read()

def risk_term_node(state: GraphState) -> dict:
    print("[4/6] risk_term 실행 중...")
    prompt = _load_prompt().format(
        input_text=state["input_text"],
        sender_role=state["sender_role"],
        receiver_role=", ".join(state["receiver_roles"]),
        role_interpretations=json.dumps(state["role_interpretations"], ensure_ascii=False, indent=2),
        extracted_words=json.dumps(state["extracted_words"], ensure_ascii=False, indent=2),
    )
    result = call_llm_with_json_retry(get_llm(), prompt)
    risk_terms = result.get("risk_terms", [])
    print(f"[4/6] risk_term 완료 — {len(risk_terms)}개 위험 용어 선별")
    return {"risk_terms": risk_terms}

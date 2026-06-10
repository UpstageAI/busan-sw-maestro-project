import os
from workflow.state import GraphState
from workflow.utils import call_llm_with_json_retry
from workflow.llm import get_llm

def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "../../prompts/term_extractor.txt")
    with open(os.path.normpath(path), "r", encoding="utf-8") as f:
        return f.read()

def term_extractor_node(state: GraphState) -> dict:
    print("[2/6] word_extractor 실행 중...")
    context = state.get("context_analysis", {})
    prompt = _load_prompt().format(
        sender_role=state["sender_role"],
        receiver_role=", ".join(state["receiver_roles"]),
        input_type=context.get("inputType", state["communication_type"]),
        input_text=state["input_text"],
    )
    result = call_llm_with_json_retry(get_llm(), prompt)
    words = result.get("words", [])
    print(f"[2/6] word_extractor 완료 — {len(words)}개 단어 추출")
    return {"extracted_words": words}

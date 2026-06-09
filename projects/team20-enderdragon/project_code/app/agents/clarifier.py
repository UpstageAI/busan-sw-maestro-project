import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas import AgentState, ClarificationResult
from app.core.llm import get_llm
from app.prompts.templates import CLARIFIER_SYSTEM

logger = logging.getLogger(__name__)


def check_and_clarify(state: AgentState) -> dict:
    # 인벤토리가 연동된 클라이언트(게임 모드)면 보유 상황이 이미 전달됨 → 되묻기 불필요.
    # 아이템 유무가 아니라 '연동 여부'로 판정한다. 빈 인벤토리([])여도 게임 모드면
    # "뭐 갖고 있어?"라고 되묻지 않는다. (이슈 #24)
    if state.get("inventory_connected"):
        return {"need_clarification": False, "clarification_question": ""}

    history = state.get("history_text", "")

    # 직전 턴이 실제 '되묻기'였으면 스킵 → 무한 되묻기 방지.
    # (되묻기 문구가 '?'로 끝나지 않는 경우가 많아, 텍스트가 아니라 상태로 판정한다.)
    if state.get("prev_was_clarification"):
        logger.info("CLARIFIER: 직전 턴 되묻기 감지 → 스킵")
        return {"need_clarification": False, "clarification_question": ""}

    llm = get_llm(temperature=0.0)
    query = state["query"]
    user_content = query if not history else f"[이전 대화]\n{history}\n\n[현재 질문] {query}"

    try:
        structured_llm = llm.with_structured_output(ClarificationResult)
        result = structured_llm.invoke([
            SystemMessage(content=CLARIFIER_SYSTEM),
            HumanMessage(content=user_content),
        ])
        logger.info("CLARIFIER: need=%s question=%s", result.need_clarification, result.question)
        return {
            "need_clarification": result.need_clarification,
            "clarification_question": result.question,
        }
    except Exception as e:
        logger.warning("Clarifier failed: %s", e)
        return {"need_clarification": False, "clarification_question": ""}

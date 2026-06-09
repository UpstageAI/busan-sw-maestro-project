import logging

from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas import AgentState, TodoListResult
from app.core.llm import get_llm
from app.prompts.templates import (
    RESPONDER_SYSTEM, RESPONDER_FORMAT_GUIDE,
    GENERAL_RESPONSE_SYSTEM, OUT_OF_SCOPE_RESPONSE,
    TODO_EXTRACTOR_SYSTEM,
    format_facts_block, format_inventory_block, format_game_state_block,
    format_material_plan_block, format_progress_block, format_goal_block,
    format_goal_progress_block,
)

logger = logging.getLogger(__name__)


def _extract_todos(answer: str) -> list[str]:
    """코치 답변을 게임 할 일 목록용 짧은 명령형 TODO로 압축한다.

    게임 모드(인벤토리 연동)에서만 호출된다. 실패하면 빈 목록을 반환해
    모드가 기존 answer 파싱으로 폴백할 수 있게 한다.
    """
    if not answer or not answer.strip():
        return []
    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(TodoListResult)
        result = structured_llm.invoke([
            SystemMessage(content=TODO_EXTRACTOR_SYSTEM),
            HumanMessage(content=answer),
        ])
        todos = [t.strip() for t in result.todos if t and t.strip()]
        logger.info("TODO_EXTRACTOR: %d items", len(todos))
        return todos
    except Exception as e:
        logger.warning("Todo extraction failed: %s", e)
        return []


def generate_answer(state: AgentState) -> dict:
    """도메인에 따라 적절한 답변을 생성한다. (이전 대화 맥락 반영)

    - out_of_scope: 고정 안내 응답
    - general: temperature 0.5로 가벼운 답변
    - minecraft: temperature 0.2로 위키 검색 결과 기반 코칭 응답
    """
    domain = state.get("domain", "minecraft")
    query = state["query"]
    history = state.get("history_text", "")
    hist_block = f"[이전 대화]\n{history}\n\n" if history else ""

    # 범위 밖 질문 — 고정 안내
    if domain == "out_of_scope":
        return {"final_answer": OUT_OF_SCOPE_RESPONSE}

    # 일반 질문 — 가벼운 답변
    if domain == "general":
        llm = get_llm(temperature=0.5)
        r = llm.invoke([
            SystemMessage(content=GENERAL_RESPONSE_SYSTEM),
            HumanMessage(content=f"{hist_block}{query}"),
        ])
        return {"final_answer": r.content}

    # 마인크래프트 질문 — streaming=True로 astream_events에서 토큰 캡처 가능
    llm = get_llm(temperature=0.2, streaming=True)
    results = state.get("search_results", [])
    parts = [
        f"[{i+1}] ({doc.get('metadata', {}).get('title', '')})\n{doc.get('content', '')}"
        for i, doc in enumerate(results)
    ]
    ctx = "\n\n".join(parts) if parts else "(검색 결과 없음)"
    # 확정 사실(티어/레시피)을 참고 위키보다 위에, 우선 적용하도록 주입
    facts_block = format_facts_block(state.get("structured_facts", []))
    # 인벤토리 컨텍스트 — 게임 모드(연동)면 빈 인벤토리도 명시, 웹은 빈 문자열
    inventory_block = format_inventory_block(state.get("inventory", []), state.get("inventory_connected", False))
    # 인게임 상태(시간·체력 등) — 모드만 전달. 밤·낮은 체력 등 생존 신호를 코치가 우선 고려.
    state_block = format_game_state_block(state.get("game_state", {}))
    # 결정론 제작 분석 — 제작 목표가 있으면 검증된 부족 재료·채굴 티어를 우선 적용.
    craft_block = format_material_plan_block(state.get("goal_key", ""), state.get("material_plan", {}))
    # 진행 상황 — 직전 턴 이후 새로 얻은 재료가 있으면 반영.
    progress_block = format_progress_block(state.get("progress_note", []))
    # 추천 목표 — 막연한 질문에 resolve_goal이 다음 목표를 제안한 경우만 프레이밍.
    goal_block = format_goal_block(state.get("resolved_goal", ""), state.get("goal_proposed", False))
    # 목표 진행 — 직전 plan 대비 완료 단계·다음 한 단계(reconcile 산출).
    goal_progress_block = format_goal_progress_block(state.get("completed_steps", []), state.get("next_step", {}))

    r = llm.invoke([
        SystemMessage(content=f"{RESPONDER_SYSTEM}\n{RESPONDER_FORMAT_GUIDE}"),
        HumanMessage(content=f"{hist_block}{goal_block}{progress_block}{goal_progress_block}{state_block}{inventory_block}질문: {query}\n\n{craft_block}{facts_block}참고 위키:\n{ctx}"),
    ])
    out = {"final_answer": r.content}
    # 게임 모드(인벤토리 연동)에서만 할 일 목록용 짧은 TODO를 별도 생성. 웹은 미사용.
    if state.get("inventory_connected"):
        out["todos"] = _extract_todos(r.content)
    return out

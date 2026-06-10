from typing import Any

from app.agent.state import AgentState
from app.preferences.matcher import apply_preferences
from app.preferences.store import save_preference


def confirm_node(state: AgentState) -> dict[str, Any]:
    """
    3단계 노드: 선호 적용 → 사용자 컨펌 대기 → 수정 발생 시 선호 저장.

    HTTP 레이어(/confirm)에서 컨펌 결과를 state["confirmed_output"]에 주입한 뒤
    이 노드를 재개하는 방식으로 연동한다.
    """
    draft = apply_preferences(state["draft"])

    confirmed = state.get("confirmed_output")
    if confirmed is None:
        # 아직 사용자 응답 없음 — 그래프가 HTTP 응답을 기다리는 중단 지점
        return {"draft": draft}

    if confirmed != draft:
        save_preference(original=draft, modified=confirmed)

    return {"final_output": confirmed}

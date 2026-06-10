"""6-3 선호 확인(2차 HITL) + 저장 노드.

- preference_interrupt_node: 후보를 사용자에게 제시하고 interrupt() 로 정지(2차 HITL).
  resume 값 = PreferenceChoice 리스트. interrupt 만 하고 side effect 는 두지 않는다
  (resume 시 이 노드가 처음부터 재실행되므로).
- preference_store_node: action=save 인 후보만 User Preference Store 에 저장한다.
  INSERT 라 interrupt 가 없는 별도 노드에 둔다(중복 저장 방지).

1차 승인 interrupt(reason=awaiting_approval)와 payload 의 reason 으로 구분된다.
"""

from langgraph.types import interrupt

from app.feedback.db import save_user_preference
from app.logging_config import get_logger

logger = get_logger("node.preference")


def preference_interrupt_node(state: dict) -> dict:
    candidates = state.get("candidates", [])
    logger.info("분기: 선호 확인 대기(interrupt) - 후보 %d건", len(candidates))
    choices = interrupt(
        {
            "reason": "awaiting_preference",
            "candidates": candidates,
        }
    )
    logger.info("분기: 선호 확인 결정 수신 - %d건", len(choices or []))
    return {"preference_choices": choices or []}


def preference_store_node(state: dict) -> dict:
    choices = state.get("preference_choices", [])
    saved_fields: list[str] = []
    for ch in choices:
        if ch.get("action") == "save":
            save_user_preference(
                field=ch["field"],
                original_pattern=ch.get("original"),
                preferred=ch.get("preferred"),
            )
            saved_fields.append(ch["field"])

    confirmed = {
        "saved": bool(saved_fields),
        "saved_fields": saved_fields,
        "saved_count": len(saved_fields),
        "final_output": state.get("final_output", {}),
    }
    logger.info(
        "분기: 선호 저장 완료 - %d건 저장(%s)", len(saved_fields), saved_fields
    )
    return {"confirmed_output": confirmed}

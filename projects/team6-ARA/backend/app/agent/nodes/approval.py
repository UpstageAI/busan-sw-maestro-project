"""사용자 승인 노드 (HITL interrupt).

conflict_check 까지 끝난 검토 패키지(reviewables)를 사용자에게 제시하고 `interrupt()`로
그래프를 정지한다. 호출자(/run)는 interrupt payload(reviewables)를 FE에 반환하고,
FE가 결정(decisions)을 /resume 으로 보내면 그 값이 resume 으로 주입돼 그래프가 재개된다.
"""

from langgraph.types import interrupt

from app.logging_config import get_logger

logger = get_logger("node.approval")


def request_approval_node(state: dict) -> dict:
    reviewables = state.get("reviewables", [])
    skipped = state.get("skipped", [])
    conflicts = sum(1 for r in reviewables if r.get("conflict", {}).get("has_conflict"))
    logger.info(
        "분기: 사용자 승인 대기(interrupt) - 검토 %d건(충돌 %d건), 제외 %d건",
        len(reviewables),
        conflicts,
        len(skipped),
    )
    # 정지하고 reviewables 를 호출자에게 반환. resume 값 = ApprovalDecision 리스트.
    decisions = interrupt(
        {
            "reason": "awaiting_approval",
            "reviewables": reviewables,
            "skipped": skipped,
        }
    )
    logger.info("분기: 승인 결정 수신 - %d건", len(decisions or []))
    return {"decisions": decisions or []}

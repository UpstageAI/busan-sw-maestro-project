"""6-3 피드백 분석 노드 (단일 그래프 흡수).

feedback_seam 이 만든 modifications((original, modified) 쌍)를 받아 변경 필드 단위
선호 후보를 생성하고 preference_candidate_log 에 적재한다. 후보가 있으면 다음 노드
(preference_interrupt, 2차 HITL)로, 없으면 그래프가 END 로 끝난다.

분석 로직은 app/feedback 의 기존 함수를 재사용한다(노드는 얇은 래퍼). save_candidate_log
는 INSERT 라 interrupt 가 없는 이 노드에 둔다(2차 interrupt resume 시 중복 적재 방지).
"""

from app.feedback.analyzer import (
    detect_diff,
    determine_pattern_type,
    generate_candidates,
)
from app.feedback.db import load_user_preferences, save_candidate_log
from app.feedback.verifier import verify_result
from app.logging_config import get_logger

logger = get_logger("node.feedback_analyze")


def feedback_analyze_node(state: dict) -> dict:
    modifications = state.get("modifications", [])
    final_output = state.get("final_output", {})
    verified = verify_result(final_output)
    existing = load_user_preferences()
    session_id = state.get("session_id", "")

    candidates: list[dict] = []
    for mod in modifications:
        original = mod.get("original") or {}
        modified = mod.get("modified") or {}
        diff = detect_diff(original, modified)
        if not diff:
            continue
        cands = generate_candidates(diff)
        pattern_type = determine_pattern_type(diff, existing)
        log_id = save_candidate_log(
            session_id=session_id,
            original=original,
            modified=modified,
            diff=diff,
            pattern_type=pattern_type,
            candidates=cands,
        )
        for c in cands:
            candidates.append({**c, "pattern_type": pattern_type, "log_id": log_id})

    logger.info(
        "분기: 6-3 피드백 분석 - 수정 %d건 -> 후보 %d건(검증 %s)",
        len(modifications),
        len(candidates),
        verified,
    )
    return {"candidates": candidates, "verified": verified}

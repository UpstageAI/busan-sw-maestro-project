from typing import Any, TypedDict

# 팀 합의 필요: 각 단계 담당자가 사용하는 필드를 여기에 추가한다.
# 6-1 -> 6-2 -> 6-3 를 하나의 LangGraph 로 잇고, AgentState 로 단계 간 핸드오프한다.
class AgentState(TypedDict, total=False):
    # --- 공통 ---
    session_id: str                  # = checkpointer thread_id
    raw_input: str                   # /run 직접 분석 확장 자리. 현재 FE는 /analyze/ 후 items 전달.

    # --- 6-1 분석 산출 ---
    items: list[dict[str, Any]]      # 분석 산출 항목 (Item.model_dump)

    # --- 6-2 라우팅/검증/승인 ---
    selections: list[dict[str, Any]] # ToolSelection
    conflicts: list[dict[str, Any]]  # ConflictCheckResult
    reviewables: list[dict[str, Any]]# ReviewableItem (승인 interrupt payload)
    skipped: list[dict[str, Any]]    # 처리 제외 항목 (type=ignore 등)
    decisions: list[dict[str, Any]]  # ApprovalDecision (승인 interrupt resume 입력)
    results: list[dict[str, Any]]    # ExecutionResult
    summary: dict[str, Any]          # 실행 요약 {executed, excluded, failed, recheck}

    # --- 6-2 -> 6-3 seam (연결부) ---
    final_output: dict[str, Any]     # 최종 결과 요약 (6-3 Result Summary 입력)
    modifications: list[dict[str, Any]]  # 수정 항목 (original, modified) 쌍 -> 6-3 Feedback Analyzer 입력

    # --- 6-3 피드백/선호 (feat/preferences, 향후 그래프 흡수) ---
    draft: dict[str, Any]            # 6-3 가 사용
    confirmed_output: dict[str, Any] # 6-3 가 사용

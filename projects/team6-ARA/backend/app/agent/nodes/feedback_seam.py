"""6-3 연결부(seam) 노드.

6-2 실행 결과를 6-3(피드백/선호)이 소비할 형태로 정리한다. 현재는 여기서 그래프가
END 로 끝나지만, 6-3 담당자가 이 노드 **다음에** 자기 노드(Verification -> Feedback
Analyzer -> 선호 확인 interrupt -> Preference Store)를 붙이면 된다.

6-3 에 넘기는 계약(AgentState):
- final_output: Result Summary 입력 (성공/제외/실패/재검증 집계 + 저장 항목)
- modifications: 수정(modify) 항목의 (original, modified) 쌍 -> 6-3 Feedback Analyzer 입력
  (6-3 의 /feedback/analyze(original, modified) 와 맞물린다)
"""

from app.logging_config import get_logger

logger = get_logger("node.feedback_seam")


def feedback_entry_node(state: dict) -> dict:
    results = state.get("results", [])
    reviewables = {r["item"]["id"]: r["item"] for r in state.get("reviewables", [])}

    modifications: list[dict] = []
    for res in results:
        if res.get("status") == "needs_recheck" and res.get("modified_item"):
            original = reviewables.get(res["item_id"])
            modifications.append(
                {"original": original, "modified": res["modified_item"]}
            )

    final_output = {
        "summary": state.get("summary", {}),
        "executed": [r for r in results if r.get("status") == "success"],
        "excluded": [r for r in results if r.get("status") == "excluded"],
        "pending": [
            r for r in results if r.get("status") in ("failed", "pending")
        ],
        "needs_recheck": [
            r for r in results if r.get("status") == "needs_recheck"
        ],
    }

    logger.info(
        "분기: 6-3 seam - 최종 정리 완료(수정 %d건은 6-3 Feedback 으로 전달)",
        len(modifications),
    )
    # 6-3 가 여기 뒤에 붙는다. 현재는 final_output/modifications 까지 채우고 END.
    return {"final_output": final_output, "modifications": modifications}

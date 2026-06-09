"""Tool Execution 노드 (/approve 경로 전용).

사용자 결정(approve/modify/exclude)에 따라 Local Tool 을 호출한다.
- approve  : item.type 에서 tool 을 재도출(echo 불신) + 필수 필드 재확인 후 실행/저장
- modify   : 저장하지 않고 recheck_required=True (6-1 재검증 신호), modified_item echo
- exclude  : 저장하지 않음
- 실패     : ERROR 로그 + save_to_pending 폴백
"""

from app.agent.nodes.tool_selection import TYPE_TO_TOOL
from app.logging_config import get_logger
from app.schemas.approval import (
    ApprovalAction,
    ApprovalDecision,
    ExecutionResult,
    ExecutionStatus,
)
from app.schemas.items import REQUIRED_FIELDS, Item, ItemType, ToolName
from app.schemas.routing import ReviewableItem
from app.tools import TOOL_REGISTRY, save_to_pending

logger = get_logger("node.execution")


def _build_kwargs(item: Item, tool: ToolName) -> dict:
    """Tool 시그니처에 맞춰 item 에서 인자를 추출한다."""
    if tool == ToolName.create_task:
        return {
            "title": item.title,
            "assignee": item.assignee,
            "due_date": item.due_date,
            "priority": item.priority.value if item.priority else None,
        }
    if tool == ToolName.create_calendar_event:
        return {
            "title": item.title,
            "date": item.date,
            "time": item.time,
            "all_day": item.all_day,
            "duration_estimate": item.duration_estimate,
        }
    if tool == ToolName.create_memo:
        return {"title": item.title, "content": item.content}
    if tool == ToolName.create_risk_log:
        return {
            "description": item.description or item.title,
            "mitigation": item.mitigation,
        }
    if tool == ToolName.save_to_pending:
        return {
            "title": item.title,
            "reason": "정보 부족으로 보류",
            "clarification_question": item.clarification_question,
        }
    return {"title": item.title}


def _missing_required(item: Item) -> list[str]:
    """필수 필드 중 비어 있는 항목명 목록."""
    required = REQUIRED_FIELDS.get(item.type, ("title",))
    missing = []
    for field in required:
        if getattr(item, field, None) in (None, ""):
            missing.append(field)
    return missing


def _execute_one(item: Item, item_id: str) -> ExecutionResult:
    """단일 승인 항목을 실행한다 (재도출 + 재검증 + 실패 폴백).

    item_id 는 decision.item_id(원본 식별자)를 명시적으로 받는다. modified_item 의
    id 는 FE 가 비워 보낼 수 있어 신뢰하지 않는다(결과-원본 매칭 유지).
    """
    if item.type == ItemType.ignore:
        return ExecutionResult(
            item_id=item_id, status=ExecutionStatus.excluded, error="ignore 항목"
        )

    # 경량 재검증: echo 된 tool 을 믿지 않고 type 에서 재도출.
    tool = TYPE_TO_TOOL[item.type]
    logger.info(
        "execution approve start: item=%s type=%s tool=%s title=%s",
        item_id,
        item.type,
        tool,
        item.title,
    )

    # 필수 필드 재확인 -> 누락 시 pending 폴백.
    missing = _missing_required(item)
    if missing:
        reason = f"필수 필드 누락: {', '.join(missing)}"
        logger.warning("필수 필드 누락 -> pending: item=%s (%s)", item_id, reason)
        pid = save_to_pending(title=item.title, reason=reason)
        # 저장됐으므로 pending(=보류 저장)이 의미상 맞다. tool 실행 실패 폴백과 동일.
        return ExecutionResult(
            item_id=item_id,
            status=ExecutionStatus.pending,
            tool=tool,
            stored_id=pid,
            error=reason,
        )

    # Tool 실행.
    func = TOOL_REGISTRY[tool]
    kwargs = _build_kwargs(item, tool)
    try:
        stored_id = func(**kwargs)
    except Exception as exc:  # noqa: BLE001 - 데모용 광범위 폴백
        logger.error("Tool 실패: item=%s tool=%s err=%s", item_id, tool.value, exc)
        pid = save_to_pending(title=item.title, reason=f"tool 실행 실패: {exc}")
        return ExecutionResult(
            item_id=item_id,
            status=ExecutionStatus.pending,
            tool=tool,
            stored_id=pid,
            error=str(exc),
        )

    logger.info(
        "분기: execution 저장 완료 - item=%s tool=%s id=%s",
        item_id,
        tool.value,
        stored_id,
    )
    return ExecutionResult(
        item_id=item_id,
        status=ExecutionStatus.success,
        tool=tool,
        stored_id=stored_id,
    )


def execution_node(state: dict) -> dict:
    """reviewables + decisions -> results / summary."""
    reviewables = {
        r["item"]["id"]: ReviewableItem.model_validate(r)
        for r in state.get("reviewables", [])
    }
    decisions = [ApprovalDecision.model_validate(d) for d in state.get("decisions", [])]
    action_counts: dict[str, int] = {}
    for decision in decisions:
        action_counts[decision.action.value] = action_counts.get(decision.action.value, 0) + 1
    logger.info(
        "분기: execution 시작 - reviewables=%d decisions=%d actions=%s",
        len(reviewables),
        len(decisions),
        action_counts,
    )

    results: list[ExecutionResult] = []
    for decision in decisions:
        reviewable = reviewables.get(decision.item_id)

        if decision.action == ApprovalAction.exclude:
            logger.info("분기: 제외 - item=%s", decision.item_id)
            results.append(
                ExecutionResult(
                    item_id=decision.item_id, status=ExecutionStatus.excluded
                )
            )
            continue

        if decision.action == ApprovalAction.modify:
            # 저장하지 않고 재검증 신호만 (modified_item 을 /route 에 재투입).
            logger.info("분기: 수정 -> 재검증 필요 - item=%s", decision.item_id)
            results.append(
                ExecutionResult(
                    item_id=decision.item_id,
                    status=ExecutionStatus.needs_recheck,
                    recheck_required=True,
                    modified_item=decision.modified_item,
                )
            )
            continue

        # approve: modified_item 우선, 없으면 reviewable 의 원본 item.
        if decision.modified_item is not None:
            item = decision.modified_item
        elif reviewable is not None:
            item = reviewable.item
        else:
            logger.warning("승인 항목에 대응하는 reviewable 없음: %s", decision.item_id)
            results.append(
                ExecutionResult(
                    item_id=decision.item_id,
                    status=ExecutionStatus.failed,
                    error="reviewable 누락",
                )
            )
            continue
        results.append(_execute_one(item, decision.item_id))

    summary = {
        "executed": sum(1 for r in results if r.status == ExecutionStatus.success),
        "excluded": sum(1 for r in results if r.status == ExecutionStatus.excluded),
        "failed": sum(
            1
            for r in results
            if r.status in (ExecutionStatus.failed, ExecutionStatus.pending)
        ),
        "recheck": sum(
            1 for r in results if r.status == ExecutionStatus.needs_recheck
        ),
    }
    logger.info("분기: execution 완료 - %s", summary)
    return {
        "results": [r.model_dump(mode="json") for r in results],
        "summary": summary,
    }

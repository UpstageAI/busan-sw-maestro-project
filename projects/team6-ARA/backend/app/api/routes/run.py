"""6-1~6-2 단일 그래프 HTTP 엔드포인트 (interrupt/resume 기반 HITL).

- POST /run            : 그래프 시작 -> 승인 지점(interrupt)에서 정지, reviewables 반환
- POST /resume         : 사용자 결정(decisions)으로 그래프 재개 -> 실행 + 요약
- GET  /storage/{kind} : 저장소 행 조회 (데모 확인용)
- POST /mock/seed      : 시연용 시스템 데이터 초기화 (데모 전용, 일반 흐름 아님)
- POST /mock/run/{scenario} : Mock 시나리오를 /run 으로 흘려보내는 데모 트리거

세션 상태는 MemorySaver(checkpointer)에 session_id(=thread_id)로 보관된다.
"""

import uuid

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from app.agent.graph import build_graph
from app.logging_config import get_logger, summarize_items
from app.mock_data import SAMPLE_SCENARIOS, get_scenario
from app.schemas.run import ResumeRequest, RunRequest, RunResponse, RunStatus
from app.storage.db import TABLES
from app.storage.queries import list_table
from app.storage.seed import seed_if_empty

router = APIRouter(tags=["routing"])
logger = get_logger("api.run")


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _to_response(session_id: str, result: dict) -> RunResponse:
    """그래프 invoke 결과를 응답으로 변환.

    interrupt 면 payload 의 reason 으로 1차(승인)/2차(선호 확인)를 구분한다. 순차 HITL
    이라 동시에 둘이 뜨지 않으므로 [0] 단일 interrupt 전제가 유효하다.
    """
    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value
        if payload.get("reason") == "awaiting_preference":
            response = RunResponse(
                session_id=session_id,
                status=RunStatus.awaiting_preference,
                candidates=payload.get("candidates", []),
            )
            logger.info(
                "Graph response awaiting_preference: session=%s candidates=%d",
                session_id,
                len(response.candidates),
            )
            return response
        response = RunResponse(
            session_id=session_id,
            status=RunStatus.awaiting_approval,
            reviewables=payload.get("reviewables", []),
            skipped=payload.get("skipped", []),
        )
        logger.info(
            "Graph response awaiting_approval: session=%s reviewables=%d skipped=%d",
            session_id,
            len(response.reviewables),
            len(response.skipped),
        )
        return response
    response = RunResponse(
        session_id=session_id,
        status=RunStatus.completed,
        results=result.get("results", []),
        summary=result.get("summary", {}),
        final_output=result.get("final_output"),
        confirmed_output=result.get("confirmed_output"),
    )
    logger.info(
        "Graph response completed: session=%s results=%d summary=%s",
        session_id,
        len(response.results),
        response.summary,
    )
    return response


@router.post("/run", response_model=RunResponse)
def run(req: RunRequest) -> RunResponse:
    """그래프 시작. 승인 지점에서 정지하고 검토 패키지를 반환한다."""
    logger.info(
        "POST /run start: session=%s items=%s raw_len=%d",
        req.session_id,
        summarize_items([it.model_dump() for it in req.items]),
        len(req.raw_input or ""),
    )
    graph = build_graph()
    try:
        result = graph.invoke(
            {
                "session_id": req.session_id,
                "items": [it.model_dump(mode="json") for it in req.items],
                "raw_input": req.raw_input,
            },
            _config(req.session_id),
        )
    except Exception:
        logger.exception("POST /run failed: session=%s", req.session_id)
        raise
    response = _to_response(req.session_id, result)
    logger.info("POST /run complete: session=%s status=%s", req.session_id, response.status)
    return response


@router.post("/resume", response_model=RunResponse)
def resume(req: ResumeRequest) -> RunResponse:
    """사용자 결정으로 그래프 재개 (1차 승인 또는 2차 선호 확인).

    preference_choices 가 오면 2차(선호 확인) interrupt 재개로, 아니면 1차(승인)
    재개로 분기한다. 그래프는 현재 정지점(1차/2차)에 resume 값을 주입한다.

    전제: 해당 session_id 가 그 단계 interrupt 로 정지된 상태여야 한다. 정지 상태가
    아닌(또는 존재하지 않는) session_id 로 호출하거나 같은 정지점을 중복 resume 하면
    동작이 보장되지 않는다(데모는 happy path 전제). 운영 시 대기 세션 존재 검증
    (graph.get_state) 후 없으면 4xx 반환을 추가한다.
    """
    # 둘 다 비면 빈 결정으로 그래프가 조용히 완료되어 사용자 입력이 무시된다.
    if req.preference_choices is None and not req.decisions:
        raise HTTPException(
            status_code=400,
            detail="decisions 또는 preference_choices 중 하나는 필요합니다.",
        )
    if req.preference_choices is not None:
        resume_value = [c.model_dump(mode="json") for c in req.preference_choices]
        logger.info(
            "POST /resume start (preference): session=%s choices=%d",
            req.session_id,
            len(req.preference_choices),
        )
    else:
        action_counts: dict[str, int] = {}
        for decision in req.decisions:
            action_counts[decision.action.value] = action_counts.get(decision.action.value, 0) + 1
        resume_value = [d.model_dump(mode="json") for d in req.decisions]
        logger.info(
            "POST /resume start: session=%s decisions=%d actions=%s",
            req.session_id,
            len(req.decisions),
            action_counts,
        )
    graph = build_graph()
    try:
        result = graph.invoke(
            Command(resume=resume_value),
            _config(req.session_id),
        )
    except Exception:
        logger.exception("POST /resume failed: session=%s", req.session_id)
        raise
    response = _to_response(req.session_id, result)
    logger.info("POST /resume complete: session=%s status=%s", req.session_id, response.status)
    return response


@router.get("/storage/{kind}")
def storage(kind: str) -> dict:
    """저장소 테이블 행 조회 (데모 확인용)."""
    logger.info("GET /storage/%s start", kind)
    try:
        rows = list_table(kind)
    except KeyError:
        logger.warning("GET /storage/%s unknown kind", kind)
        raise HTTPException(
            status_code=404,
            detail=f"알 수 없는 저장소 종류: {kind}. 가능: {sorted(TABLES)}",
        )
    logger.info("GET /storage/%s complete: count=%d", kind, len(rows))
    return {"kind": kind, "count": len(rows), "rows": rows}


@router.post("/mock/seed")
def mock_seed() -> dict:
    """시연용 시스템 데이터 초기화.

    데모 전용 엔드포인트다. 운영/일반 사용자 흐름이 아니며, 루트 지침의
    "저장 전 사용자 승인" 대상과 무관한 시연용 시스템 데이터를 넣는다.
    """
    logger.info("POST /mock/seed start")
    seeded = seed_if_empty()
    logger.info("POST /mock/seed complete: %s", seeded)
    return {"seeded": seeded}


@router.post("/mock/run/{scenario}", response_model=RunResponse)
def mock_run(scenario: str) -> RunResponse:
    """Mock 시나리오 입력을 /run 으로 흘려보내는 데모 트리거."""
    logger.info("POST /mock/run/%s start", scenario)
    try:
        payload = dict(get_scenario(scenario))  # 전역 시나리오 dict 보호용 얕은 복사
    except KeyError:
        logger.warning("POST /mock/run/%s unknown scenario", scenario)
        raise HTTPException(
            status_code=404,
            detail=f"알 수 없는 시나리오: {scenario}. 가능: {sorted(SAMPLE_SCENARIOS)}",
        )
    # 매 호출 고유 session_id 로 새 thread 를 연다. 같은 시나리오를 반복 시연해도
    # 이전 interrupt 가 남은 thread 에 재진입하지 않는다(MemorySaver 는 프로세스 지속).
    # 반환된 RunResponse.session_id 로 이어서 /resume 한다.
    base = payload.get("session_id", scenario)
    payload["session_id"] = f"{base}-{uuid.uuid4().hex[:8]}"
    logger.info("POST /mock/run/%s delegated: session=%s", scenario, payload["session_id"])
    return run(RunRequest.model_validate(payload))

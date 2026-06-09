from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.feedback.analyzer import detect_diff, determine_pattern_type, generate_candidates
from app.feedback.db import (
    get_candidate_log,
    load_user_preferences,
    save_candidate_log,
    save_user_preference,
)
from app.feedback.verifier import verify_result

router = APIRouter(prefix="/feedback", tags=["feedback"])


class AnalyzeRequest(BaseModel):
    session_id: str
    original: dict[str, Any]
    modified: dict[str, Any]


class Candidate(BaseModel):
    field: str
    original: Any
    preferred: Any


class AnalyzeResponse(BaseModel):
    session_id: str
    log_id: int
    pattern_type: Literal["one_time", "recurring"]
    candidates: list[Candidate]
    final_output: dict[str, Any]


class ConfirmRequest(BaseModel):
    session_id: str
    log_id: int
    action: Literal["save", "one_time", "dismiss"]
    candidates: list[Candidate]  # 사용자가 앞으로 적용하기로 선택한 후보 (일부만 가능)


class ResultSummary(BaseModel):
    total_candidates: int   # 분석된 선호 후보 수
    saved_count: int        # 실제 저장된 선호 수
    saved_fields: list[str] # 저장된 필드 목록
    action_taken: Literal["save", "one_time", "dismiss"]
    message: str            # 사람이 읽을 수 있는 처리 결과 메시지


class ConfirmResponse(BaseModel):
    session_id: str
    saved: bool
    final_output: dict[str, Any]
    verified: bool
    summary: ResultSummary


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    diff = detect_diff(body.original, body.modified)
    existing_prefs = load_user_preferences()
    pattern_type = determine_pattern_type(diff, existing_prefs)
    candidates = generate_candidates(diff)

    log_id = save_candidate_log(
        session_id=body.session_id,
        original=body.original,
        modified=body.modified,
        diff=diff,
        pattern_type=pattern_type,
        candidates=candidates,
    )

    return AnalyzeResponse(
        session_id=body.session_id,
        log_id=log_id,
        pattern_type=pattern_type,
        candidates=[Candidate(**c) for c in candidates],
        final_output=body.modified,
    )


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_preference(body: ConfirmRequest) -> ConfirmResponse:
    log = get_candidate_log(body.log_id)
    final_output = log["modified"] if log else {}
    verified = verify_result(final_output)

    total = len(body.candidates)

    if body.action in ("dismiss", "one_time") or not body.candidates:
        message = (
            "이번에만 적용하고 저장하지 않았습니다."
            if body.action == "one_time"
            else "수정 사항을 무시했습니다."
        )
        return ConfirmResponse(
            session_id=body.session_id,
            saved=False,
            final_output=final_output,
            verified=verified,
            summary=ResultSummary(
                total_candidates=total,
                saved_count=0,
                saved_fields=[],
                action_taken=body.action,
                message=message,
            ),
        )

    for candidate in body.candidates:
        save_user_preference(
            field=candidate.field,
            original_pattern=candidate.original,
            preferred=candidate.preferred,
        )

    saved_fields = [c.field for c in body.candidates]
    return ConfirmResponse(
        session_id=body.session_id,
        saved=True,
        final_output=final_output,
        verified=verified,
        summary=ResultSummary(
            total_candidates=total,
            saved_count=len(saved_fields),
            saved_fields=saved_fields,
            action_taken="save",
            message=f"{len(saved_fields)}개 선호가 저장되었습니다: {', '.join(saved_fields)}",
        ),
    )

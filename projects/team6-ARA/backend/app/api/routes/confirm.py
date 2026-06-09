from fastapi import APIRouter
from pydantic import BaseModel

from app.preferences.matcher import apply_preferences
from app.preferences.store import save_preference

router = APIRouter(prefix="/confirm", tags=["confirm"])


class ConfirmRequest(BaseModel):
    session_id: str
    draft: dict          # 이전 단계에서 넘어온 초안
    confirmed: dict      # 사용자가 최종 제출한 내용 (수정 없으면 draft와 동일)


class ConfirmResponse(BaseModel):
    session_id: str
    final_output: dict
    preference_saved: bool


@router.post("/", response_model=ConfirmResponse)
async def confirm_output(body: ConfirmRequest) -> ConfirmResponse:
    draft_with_prefs = apply_preferences(body.draft)

    preference_saved = False
    if body.confirmed != draft_with_prefs:
        save_preference(original=draft_with_prefs, modified=body.confirmed)
        preference_saved = True

    return ConfirmResponse(
        session_id=body.session_id,
        final_output=body.confirmed,
        preference_saved=preference_saved,
    )

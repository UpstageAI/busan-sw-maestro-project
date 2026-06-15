"""6-3 선호 확인(2차 HITL) 전송 스키마.

단일 그래프 흡수 후 6-3 은 feedback_seam 다음 노드(feedback_analyze ->
preference_interrupt -> preference_store)로 동작한다. 이 모듈은 2차 interrupt 의
입출력(후보 제시 / 사용자 선택)만 정의한다. 분석 로직 자체는 app/feedback, app/preferences.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class PreferenceAction(str, Enum):
    save = "save"  # User Preference Store 에 저장(앞으로도 적용)
    one_time = "one_time"  # 이번만 적용, 저장 안 함
    dismiss = "dismiss"  # 무시


class PreferenceCandidate(BaseModel):
    """선호 후보 (2차 interrupt 가 FE 에 제시). 수정 쌍의 변경 필드 단위."""

    field: str
    original: Any = None
    preferred: Any = None
    pattern_type: str | None = None  # "one_time" | "recurring"
    log_id: int | None = None  # preference_candidate_log PK (confirm 추적용)


class PreferenceChoice(BaseModel):
    """후보별 사용자 결정 (2차 resume 입력)."""

    field: str
    action: PreferenceAction
    original: Any = None
    preferred: Any = None
    log_id: int | None = None

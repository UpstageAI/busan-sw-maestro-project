from typing import Any

from app.preferences.store import load_preferences


def apply_preferences(draft: dict[str, Any]) -> dict[str, Any]:
    """
    저장된 선호 이력을 참조해 draft에 자동 적용한다.

    TODO: 유사도 기반 매칭 구현 (현재는 exact match만 처리).
    """
    prefs = load_preferences()
    for pref in prefs:
        if pref["original"] == draft:
            return pref["modified"]
    return draft

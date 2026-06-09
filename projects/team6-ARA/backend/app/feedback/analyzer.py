from typing import Any


def detect_diff(original: dict[str, Any], modified: dict[str, Any]) -> dict[str, Any]:
    """두 dict를 비교해 변경된 필드와 변경 전·후 값을 반환."""
    diff = {}
    for key in set(original) | set(modified):
        orig_val = original.get(key)
        mod_val = modified.get(key)
        if orig_val != mod_val:
            diff[key] = {"original": orig_val, "modified": mod_val}
    return diff


def generate_candidates(diff: dict[str, Any]) -> list[dict[str, Any]]:
    """변경된 필드 각각을 선호 후보로 변환."""
    return [
        {"field": field, "original": change["original"], "preferred": change["modified"]}
        for field, change in diff.items()
    ]


def determine_pattern_type(
    diff: dict[str, Any],
    existing_preferences: list[dict[str, Any]],
) -> str:
    """기존 UserPreference와 비교해 반복 패턴("recurring") 또는 1회성("one_time")을 반환."""
    for pref in existing_preferences:
        for field, change in diff.items():
            if (
                pref.get("field") == field
                and pref.get("original_pattern") == change["original"]
            ):
                return "recurring"
    return "one_time"

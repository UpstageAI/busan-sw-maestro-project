from __future__ import annotations

from typing import Any


MENTOR_PAYLOAD_FIELDS = (
    "mentor_id",
    "name",
    "domain",
    "keywords",
    "can_help",
    "less_relevant_for",
    "profile_summary",
)


def mentor_to_document(mentor: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"이름: {mentor.get('name', '')}",
            f"분야: {_join_values(mentor.get('domain', []))}",
            f"키워드: {_join_values(mentor.get('keywords', []))}",
            f"도움 가능 영역: {_join_values(mentor.get('can_help', []))}",
            f"덜 적합한 영역: {_join_values(mentor.get('less_relevant_for', []))}",
            f"프로필: {mentor.get('profile_summary', '')}",
        ]
    )


def mentor_to_payload(mentor: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_name in MENTOR_PAYLOAD_FIELDS:
        if field_name in mentor:
            payload[field_name] = mentor[field_name]
    return payload


def _join_values(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    return str(value) if value else ""

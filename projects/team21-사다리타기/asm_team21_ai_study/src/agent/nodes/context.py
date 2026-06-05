from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def format_context(chunks: Iterable[Mapping[str, Any]]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        header = f"[출처: {chunk['source']}]"
        if chunk.get("url"):
            header += f"\n[공식 링크: {chunk['url']}]"
        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)

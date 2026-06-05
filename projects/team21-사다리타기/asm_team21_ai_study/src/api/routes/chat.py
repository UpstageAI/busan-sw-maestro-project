from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...agent.graph import get_graph
from ...agent.state import AgentState
from ...session.manager import session_manager
from ..schemas import ChatRequest, ChatResponse, SourceDocument

router = APIRouter(prefix="/chat", tags=["chat"])


def _make_preview(content: str, max_len: int = 120) -> str:
    skipped_prefixes = ("원문:", "등록일:", "작성자:")
    parts: list[str] = []
    current_len = 0
    for line in content.splitlines():
        text = line.strip()
        if not text or text.startswith(skipped_prefixes):
            continue
        if "http://" in text or "https://" in text:
            continue
        parts.append(text)
        current_len += len(text) + (1 if current_len > 0 else 0)
        if current_len >= max_len:
            break

    preview = " ".join(parts)
    if len(preview) <= max_len:
        return preview
    return preview[: max_len - 3].rstrip() + "..."


@router.post("/{session_id}", response_model=ChatResponse)
def chat(session_id: str, body: ChatRequest):
    session = session_manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 만료되었습니다.")

    initial_state: AgentState = {
        "question":          body.message,
        "intent":            "",
        "retrieved_chunks":  [],
        "generated_answer":  "",
        "execution_history": [],
        "chat_history":      list(session.chat_history),
    }

    result: AgentState = get_graph().invoke(initial_state)

    session.append_turn(body.message, result["generated_answer"])

    sources: list[SourceDocument] = []
    seen_sources: set[tuple[str, str | None]] = set()
    for c in result.get("retrieved_chunks", []):
        key = (c["source"], c.get("url"))
        if key in seen_sources:
            continue
        seen_sources.add(key)
        sources.append(
            SourceDocument(
                source=c["source"],
                preview=_make_preview(c["content"]),
                url=c.get("url"),
            )
        )

    return ChatResponse(
        session_id=session_id,
        answer=result["generated_answer"],
        intent=result["intent"],
        sources=sources,
        execution_history=result.get("execution_history", []),
    )

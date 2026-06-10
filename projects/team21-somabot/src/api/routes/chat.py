from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...agent.graph import get_graph
from ...agent.state import AgentState
from ...session.manager import session_manager
from ..schemas import ChatRequest, ChatResponse, SourceDocument

router = APIRouter(prefix="/chat", tags=["chat"])


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

    sources = [
        SourceDocument(source=c["source"], preview=c["content"][:100])
        for c in result.get("retrieved_chunks", [])
    ]

    return ChatResponse(
        session_id=session_id,
        answer=result["generated_answer"],
        intent=result["intent"],
        sources=sources,
        execution_history=result.get("execution_history", []),
    )

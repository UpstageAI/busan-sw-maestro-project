import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest, ChatResponse, StreamEvent
from app.graph import create_graph
from app.core.database import SessionLocal
from app import repositories

router = APIRouter()
graph = create_graph()
# 대화 맥락으로 불러올 최근 메시지 수 (user+assistant 합산이라 6개 ≈ 3턴)
HISTORY_MESSAGE_LIMIT = 6
logger = logging.getLogger(__name__)


def build_initial_state(message: str, history_text: str = "", prev_was_clarification: bool = False, inventory=None, inventory_connected: bool = False) -> dict:
    return {
        "query": message,
        "history_text": history_text,
        "query_analysis": {},
        "search_results": [],
        "structured_facts": [],
        "final_answer": "",
        "domain": "",
        "need_clarification": False,
        "clarification_question": "",
        "prev_was_clarification": prev_was_clarification,
        "inventory": [i.model_dump() for i in (inventory or [])],
        "inventory_connected": inventory_connected,
    }


def _load_history(thread_id: str, limit: int = HISTORY_MESSAGE_LIMIT) -> tuple[str, bool]:
    """이전 대화 텍스트와, 직전 턴이 되묻기였는지 여부를 함께 반환한다."""
    try:
        db = SessionLocal()
        try:
            session = repositories.get_or_create_session(db, thread_id)
            msgs = repositories.get_recent_messages(db, session.id, limit=limit)
            text = "\n".join(
                f"{'사용자' if m.role == 'user' else '가이드'}: {m.content}" for m in msgs
            )
            prev_was_clarification = bool(msgs) and msgs[-1].role == "clarification"
            return text, prev_was_clarification
        finally:
            db.close()
    except Exception:
        return "", False


def _save_turn(thread_id: str, user_msg: str, assistant_msg: str, is_clarification: bool = False) -> None:
    try:
        db = SessionLocal()
        try:
            session = repositories.get_or_create_session(db, thread_id)
            repositories.append_message(db, session.id, "user", user_msg)
            role = "clarification" if is_clarification else "assistant"
            repositories.append_message(db, session.id, role, assistant_msg)
        finally:
            db.close()
    except Exception:
        pass


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    history, prev_clar = _load_history(request.thread_id)
    result = await graph.ainvoke(build_initial_state(request.message, history, prev_clar, request.inventory, request.inventory_connected))
    answer = result.get("final_answer", "")
    _save_turn(
        request.thread_id, request.message, answer,
        is_clarification=bool(result.get("need_clarification")),
    )
    return ChatResponse(answer=answer, domain=result.get("domain", ""), todos=result.get("todos", []))


@router.post("/chat")
async def chat_stream(request: ChatRequest):
    history, prev_clar = _load_history(request.thread_id)

    async def gen():
        final_answer = ""
        domain = ""
        sources: list[str] = []
        is_clarification = False

        try:
            async for event in graph.astream_events(
                build_initial_state(request.message, history, prev_clar, request.inventory, request.inventory_connected), version="v2"
            ):
                kind = event.get("event", "")
                name = event.get("name", "")

                # 노드 완료 → 진행 상황 이벤트 전송
                if kind == "on_chain_end" and name in ("analyze", "clarify", "retrieve", "respond", "ask"):
                    output = event.get("data", {}).get("output", {})

                    if name == "analyze":
                        domain = output.get("domain", "")
                    elif name == "clarify":
                        is_clarification = bool(output.get("need_clarification", False))
                    elif name == "retrieve":
                        results = output.get("search_results", [])
                        sources = list({
                            r.get("metadata", {}).get("title", "")
                            for r in results
                            if r.get("metadata", {}).get("title")
                        })
                    elif name in ("respond", "ask"):
                        final_answer = output.get("final_answer", final_answer)

                    yield f"data: {StreamEvent(event='node', node=name, data=json.dumps(output, ensure_ascii=False, default=str)).model_dump_json()}\n\n"

                # LLM 토큰 스트리밍 (respond 노드에서만)
                elif kind == "on_chat_model_stream":
                    if event.get("metadata", {}).get("langgraph_node") == "respond":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            yield f"data: {StreamEvent(event='token', data=chunk.content).model_dump_json()}\n\n"
        except Exception:
            # 노드(LLM/벡터DB 등) 예외로 스트림이 끊겨도 done·저장은 보장한다.
            # (클라이언트 끊김은 BaseException이라 여기서 잡지 않음 → finally-yield 함정 회피)
            logger.exception("SSE 스트리밍 처리 중 예외")
            if not final_answer:
                final_answer = "죄송해요, 답변을 생성하는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요."

        _save_turn(request.thread_id, request.message, final_answer, is_clarification=is_clarification)
        done_payload = {"answer": final_answer, "domain": domain, "sources": sources}
        yield f"data: {StreamEvent(event='done', data=json.dumps(done_payload, ensure_ascii=False)).model_dump_json()}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/sessions")
def get_sessions():
    """최근 대화 목록을 반환한다 (미리보기: 첫 번째 사용자 발화)."""
    db = SessionLocal()
    try:
        sessions = repositories.list_sessions(db)
        return [
            {
                "thread_id": s.thread_id,
                "preview": preview,
                "created_at": s.created_at.isoformat(),
            }
            for s, preview in sessions
        ]
    finally:
        db.close()


@router.get("/sessions/{thread_id}/messages")
def get_session_messages(thread_id: str):
    """특정 세션의 전체 메시지를 반환한다."""
    db = SessionLocal()
    try:
        session = repositories.get_session_by_thread(db, thread_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        msgs = repositories.get_recent_messages(db, session.id, limit=100)
        # 'clarification'은 내부 표시용 role이므로 프론트엔드에는 assistant로 노출한다.
        return [
            {"role": "assistant" if m.role == "clarification" else m.role, "content": m.content}
            for m in msgs
        ]
    finally:
        db.close()


@router.delete("/sessions/{thread_id}")
def delete_session(thread_id: str):
    """세션과 관련 메시지를 삭제한다."""
    db = SessionLocal()
    try:
        ok = repositories.delete_session(db, thread_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"deleted": thread_id}
    finally:
        db.close()

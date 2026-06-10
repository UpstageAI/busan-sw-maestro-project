"""SSE 스트리밍 예외 처리 회귀 테스트 (코드리뷰 H3).

retrieve/respond 등 그래프 노드에서 예외가 나도 스트림이 그냥 끊기지 않고,
폴백 답변을 담은 'done' 이벤트가 반드시 전송되는지 검증한다.
(httpx 의존 없이 async generator를 직접 소비한다.)
"""
import asyncio

from app import api
from app.schemas import ChatRequest


def test_스트리밍_노드_예외시에도_done_이벤트를_보낸다(monkeypatch):
    class _BoomGraph:
        async def astream_events(self, *args, **kwargs):
            raise RuntimeError("노드 폭발")
            yield  # async generator로 만들기 위한 표식 (실행되지 않음)

    monkeypatch.setattr(api, "graph", _BoomGraph())
    # DB 접근 격리
    monkeypatch.setattr(api, "_load_history", lambda *a, **k: ("", False))
    monkeypatch.setattr(api, "_save_turn", lambda *a, **k: None)

    async def _collect() -> str:
        resp = await api.chat_stream(ChatRequest(message="테스트", thread_id="t-h3"))
        parts = []
        async for chunk in resp.body_iterator:
            parts.append(chunk.decode() if isinstance(chunk, (bytes, bytearray)) else chunk)
        return "".join(parts)

    body = asyncio.run(_collect())

    assert '"event":"done"' in body      # 종료 이벤트가 반드시 있어야 함
    assert "문제가 생겼" in body          # 폴백 답변이 done에 실려야 함

from __future__ import annotations

import logging
import threading
import time

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

from .routes import chat as chat_router
from .routes import sessions as sessions_router
from ..session.manager import session_manager

app = FastAPI(title="소마 에이전트 API", version="0.1.0")

app.include_router(sessions_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── 만료 세션 정리 백그라운드 스레드 ─────────────────────────────────

def _purge_loop(interval: int = 60) -> None:
    while True:
        time.sleep(interval)
        removed = session_manager.purge_expired()
        if removed:
            print(f"[session purge] {removed}개 만료 세션 정리")


@app.on_event("startup")
def _start_purge_thread() -> None:
    t = threading.Thread(target=_purge_loop, daemon=True)
    t.start()

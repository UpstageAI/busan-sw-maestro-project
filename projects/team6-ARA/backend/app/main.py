from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyze, confirm, feedback, run
from app.logging_config import get_logger, setup_logging
from app.storage.db import init_db

setup_logging()
logger = get_logger("api.cors")


def _cors_origins() -> list[str]:
    configured = os.getenv("ACTION_ROUTER_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


def _cors_origin_regex() -> str:
    configured = os.getenv("ACTION_ROUTER_CORS_ORIGIN_REGEX")
    if configured is not None:
        return configured
    # 개발/시연용: Tailscale IP, MagicDNS, LAN IP 등 어떤 호스트든 FE dev server
    # 기본 포트(:3000)에서 열리면 허용한다. 운영 배포 시 env로 좁힌다.
    return r"https?://[^/]+:3000"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 스키마만 보장한다. 시연용 seed 는 자동 실행하지 않는다(POST /mock/seed 로 명시 호출).
    logger.info(
        "CORS configured: origins=%s origin_regex=%s",
        _cors_origins(),
        _cors_origin_regex(),
    )
    init_db()
    yield


app = FastAPI(title="Action Router Agent", lifespan=lifespan)

# 6-1 분석
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=_cors_origin_regex(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
# 6-1~6-2 단일 그래프 (라우팅/검증/승인)
app.include_router(run.router)
# 6-3 피드백/선호
app.include_router(confirm.router)
app.include_router(feedback.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Settings:
    def __init__(self) -> None:
        self.upstage_api_key: str = os.environ.get("UPSTAGE_API_KEY", "")
        self.upstage_base_url: str = "https://api.upstage.ai/v1/solar"
        self.chat_model: str = os.getenv("CHAT_MODEL", "solar-pro")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "solar-embedding-1-large-query")
        self.chroma_path: str = os.getenv("CHROMA_PATH", str(ROOT / "data" / "chroma"))
        self.chroma_collection: str = os.getenv("CHROMA_COLLECTION", "soma_docs")
        self.session_ttl_minutes: int = int(os.getenv("SESSION_TTL_MINUTES", "30"))
        self.max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "10"))
        self.max_chunks: int = int(os.getenv("MAX_CHUNKS", "5"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

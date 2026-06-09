import os

# LLM (Upstage Solar)
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

# MySQL (RDB)
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://app:app@localhost:3306/minecraft")

# Qdrant (Vector DB) — QDRANT_URL이 있으면 클라우드, 없으면 host:port(로컬)
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "minecraft_knowledge")

# 위키 적재 소스 (scripts/ingest_wiki.py)
WIKI_VAULT_PATH = os.getenv("WIKI_VAULT_PATH", "")

# 프론트엔드 ↔ 백엔드
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8002").split(",") if o.strip()]

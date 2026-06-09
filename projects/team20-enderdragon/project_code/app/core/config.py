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

# 웹검색 폴백 (Tavily) — RAG 커버리지 부족 시 보강. 키가 없으면 폴백을 건너뛴다(선택 기능).
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# 위키 검색 최고 유사도가 이 값 미만이면 웹검색으로 보강한다.
WEB_SEARCH_MIN_SCORE = float(os.getenv("WEB_SEARCH_MIN_SCORE", "0.5"))

# 프론트엔드 ↔ 백엔드
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8002").split(",") if o.strip()]

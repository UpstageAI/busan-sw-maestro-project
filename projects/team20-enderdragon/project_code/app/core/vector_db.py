from qdrant_client import QdrantClient

from app.core.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_HOST, QDRANT_PORT

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Qdrant 클라이언트 싱글턴.

    QDRANT_URL이 설정돼 있으면 공유 Qdrant Cloud, 없으면 로컬(host:port)에 연결한다.
    """
    global _client
    if _client is not None:
        return _client
    if QDRANT_URL:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    else:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client

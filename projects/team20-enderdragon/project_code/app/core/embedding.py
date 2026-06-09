from langchain_upstage import UpstageEmbeddings

# Upstage Solar 임베딩. api_key는 환경변수 UPSTAGE_API_KEY에서 자동으로 읽어온다.
_embeddings = UpstageEmbeddings(model="solar-embedding-1-large")


def get_embeddings() -> UpstageEmbeddings:
    """Upstage 임베딩 클라이언트를 반환한다."""
    return _embeddings


def embed_documents(texts: list[str]) -> list[list[float]]:
    """문서 텍스트 목록을 임베딩한다 (적재용)."""
    return _embeddings.embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """질의 텍스트를 임베딩한다 (검색용)."""
    return _embeddings.embed_query(text)


def embedding_dim() -> int:
    """임베딩 벡터 차원을 샘플 임베딩으로 동적으로 구한다 (모델 교체에도 견고)."""
    return len(_embeddings.embed_query("차원 측정용 샘플"))

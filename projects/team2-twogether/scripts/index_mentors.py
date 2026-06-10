from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.nodes.mentor_retrieval import load_mentors
from backend.app.rag.mentor_documents import mentor_to_document
from backend.app.rag.mentor_vector_store import (
    DEFAULT_VECTOR_SIZE,
    QdrantMentorVectorStore,
)
from backend.app.rag.upstage_embeddings import UpstageEmbeddingClient


DEFAULT_MENTORS_PATH = ROOT_DIR / "data" / "mentors.json"


def index_mentors(
    mentors_path: Path = DEFAULT_MENTORS_PATH,
    *,
    embedding_client: Any | None = None,
    vector_store: Any | None = None,
    vector_size: int = DEFAULT_VECTOR_SIZE,
) -> int:
    mentors = load_mentors(mentors_path)
    if not mentors:
        return 0

    documents = [mentor_to_document(mentor) for mentor in mentors]
    embedder = embedding_client or UpstageEmbeddingClient.from_env()
    store = vector_store or QdrantMentorVectorStore.from_env()

    vectors = embedder.embed_passages(documents)
    if len(vectors) != len(mentors):
        raise ValueError(
            f"Embedding count mismatch: expected {len(mentors)}, got {len(vectors)}"
        )

    store.ensure_collection(vector_size=vector_size)
    store.upsert_mentors(mentors, vectors)
    return len(mentors)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index mentor profiles into Qdrant.")
    parser.add_argument(
        "--mentors-path",
        type=Path,
        default=DEFAULT_MENTORS_PATH,
        help="Path to mentors.json.",
    )
    args = parser.parse_args()

    count = index_mentors(args.mentors_path)
    print(f"Indexed {count} mentors.")


if __name__ == "__main__":
    main()

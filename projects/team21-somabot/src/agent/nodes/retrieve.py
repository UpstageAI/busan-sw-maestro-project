from __future__ import annotations

import chromadb

from ..llm import embed_query
from ..state import AgentState
from ...config import get_settings

_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        s = get_settings()
        client = chromadb.PersistentClient(path=s.chroma_path)
        _collection = client.get_or_create_collection(s.chroma_collection)
    return _collection


def retrieve_node(state: AgentState) -> dict:
    s = get_settings()
    query_vec = embed_query(state["question"])
    collection = _get_collection()

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=s.max_chunks,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict] = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "score": round(1 - dist, 4),  # cosine distance → similarity
            })

    return {"retrieved_chunks": chunks, "execution_history": ["retrieve_documents"]}

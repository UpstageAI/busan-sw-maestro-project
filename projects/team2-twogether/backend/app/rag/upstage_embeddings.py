from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib import request

from backend.app.core.env import DEFAULT_ENV_PATH, load_dotenv


UPSTAGE_EMBEDDING_URL = "https://api.upstage.ai/v1/solar/embeddings"
UPSTAGE_QUERY_MODEL = "solar-embedding-1-large-query"
UPSTAGE_PASSAGE_MODEL = "solar-embedding-1-large-passage"

PostJson = Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]]


class UpstageEmbeddingClient:
    def __init__(
        self,
        api_key: str | None = None,
        embedding_url: str = UPSTAGE_EMBEDDING_URL,
        timeout: int = 30,
        post_json: PostJson | None = None,
    ):
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY", "")
        self.embedding_url = embedding_url
        self.timeout = timeout
        self._post_json = post_json or _post_json

    @classmethod
    def from_env(cls, env_path=DEFAULT_ENV_PATH) -> "UpstageEmbeddingClient":
        load_dotenv(env_path)
        return cls()

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._embed([text], UPSTAGE_QUERY_MODEL)
        return embeddings[0] if embeddings else []

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed(texts, UPSTAGE_PASSAGE_MODEL)

    def _embed(self, texts: list[str], model: str) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is required for embedding requests.")

        response = self._post_json(
            self.embedding_url,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            {"model": model, "input": texts},
            self.timeout,
        )
        data = response.get("data", [])
        return [item["embedding"] for item in data if "embedding" in item]


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    return json.loads(response_body)

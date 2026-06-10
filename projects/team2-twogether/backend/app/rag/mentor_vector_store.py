from __future__ import annotations

import json
import os
import uuid
from typing import Any, Callable
from urllib import request

from backend.app.core.env import DEFAULT_ENV_PATH, load_dotenv
from backend.app.rag.mentor_documents import mentor_to_payload


DEFAULT_COLLECTION_NAME = "mentor_profiles"
DEFAULT_VECTOR_SIZE = 4096

RequestJson = Callable[
    [str, str, dict[str, str], dict[str, Any], int],
    dict[str, Any],
]


class QdrantMentorVectorStore:
    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        timeout: int = 30,
        request_json: RequestJson | None = None,
    ):
        self.url = (url or os.getenv("QDRANT_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY", "")
        self.collection_name = collection_name
        self.timeout = timeout
        self._request_json = request_json or _request_json

    @classmethod
    def from_env(cls, env_path=DEFAULT_ENV_PATH) -> "QdrantMentorVectorStore":
        load_dotenv(env_path)
        return cls(
            collection_name=os.getenv(
                "QDRANT_COLLECTION",
                DEFAULT_COLLECTION_NAME,
            )
        )

    def is_configured(self) -> bool:
        return bool(self.url)

    def ensure_collection(self, vector_size: int = DEFAULT_VECTOR_SIZE) -> None:
        self._request(
            "PUT",
            f"/collections/{self.collection_name}",
            {
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine",
                }
            },
        )

    def upsert_mentors(
        self,
        mentors: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> None:
        points = []
        for index, (mentor, vector) in enumerate(zip(mentors, vectors)):
            points.append(
                {
                    "id": _point_id(mentor, index),
                    "vector": vector,
                    "payload": mentor_to_payload(mentor),
                }
            )

        if not points:
            return

        self._request(
            "PUT",
            f"/collections/{self.collection_name}/points",
            {"points": points},
        )

    def search(self, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            f"/collections/{self.collection_name}/points/search",
            {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
            },
        )
        result = response.get("result", [])
        if not isinstance(result, list):
            return []
        return [item for item in result if isinstance(item, dict)]

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.url:
            raise ValueError("QDRANT_URL is required for vector search.")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["api-key"] = self.api_key

        return self._request_json(
            method,
            f"{self.url}{path}",
            headers,
            payload,
            self.timeout,
        )


def _point_id(mentor: dict[str, Any], index: int) -> str:
    raw_id = str(mentor.get("mentor_id") or mentor.get("name") or index)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw_id))


def _request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    return json.loads(response_body)

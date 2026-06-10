import unittest
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.app.nodes.mentor_retrieval import (
    build_search_query,
    retrieve_mentor_candidates_rag,
)
from backend.app.core.env import load_dotenv
from backend.app.rag.mentor_documents import mentor_to_document
from backend.app.rag.mentor_vector_store import QdrantMentorVectorStore
from backend.app.rag.upstage_embeddings import UpstageEmbeddingClient
from scripts.index_mentors import index_mentors


RAG_GAP_CONTEXT = {
    "main_gap": "RAG 검색 품질과 추천 근거 생성 역량 부족",
    "gap_categories": ["RAG", "LLM Evaluation", "Agentic Workflow"],
    "needed_mentor_expertise": [
        "RAG 검색 구조 설계",
        "LLM 기반 추천 근거 생성",
        "LangGraph 기반 워크플로우 설계",
    ],
    "priority": "high",
    "reason": "멘토 후보 검색 정확도와 추천 이유의 논리성이 핵심 품질입니다.",
    "query_hints": ["RAG", "retrieval quality", "LLM evaluation", "LangGraph"],
    "source_fields": ["concerns", "tech_stack", "constraints"],
}


class FakeEmbeddingClient:
    def __init__(self):
        self.queries = []
        self.passages = []

    def embed_query(self, text):
        self.queries.append(text)
        return [1.0, 0.0, 0.0]

    def embed_passages(self, texts):
        self.passages.append(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]


class MismatchedEmbeddingClient(FakeEmbeddingClient):
    def embed_passages(self, texts):
        self.passages.append(texts)
        return []


class FakeVectorStore:
    def __init__(self):
        self.searches = []
        self.collection_sizes = []
        self.upserts = []

    def search(self, query_vector, limit):
        self.searches.append((query_vector, limit))
        return [
            {
                "score": 0.91,
                "payload": {
                    "name": "이채린",
                    "domain": ["AI", "LLM"],
                    "keywords": ["rag", "evaluation", "langgraph"],
                    "can_help": ["RAG 설계", "LLM 평가 방법"],
                    "less_relevant_for": ["세일즈"],
                    "profile_summary": "LLM 애플리케이션과 평가 설계에 강한 멘토",
                },
            }
        ]

    def ensure_collection(self, vector_size):
        self.collection_sizes.append(vector_size)

    def upsert_mentors(self, mentors, vectors):
        self.upserts.append((mentors, vectors))


class FakeUpstageTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append((url, headers, payload, timeout))
        return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}


class FakeQdrantTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, method, url, headers, payload, timeout):
        self.calls.append((method, url, headers, payload, timeout))
        if url.endswith("/points/search"):
            return {
                "result": [
                    {
                        "score": 0.88,
                        "payload": {
                            "name": "서지훈",
                            "domain": ["MLOps", "Infra"],
                            "keywords": ["deployment"],
                            "can_help": ["모델 서빙 구조 설계"],
                            "less_relevant_for": [],
                            "profile_summary": "MLOps 멘토",
                        },
                    }
                ]
            }
        return {"result": {"status": "ok"}}


def _restore_env(name, value):
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


class MentorRagTest(unittest.TestCase):
    def test_load_dotenv_sets_values_without_overwriting_existing_env(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "UPSTAGE_API_KEY=up_from_file",
                        "QDRANT_URL=http://localhost:6333",
                        "QDRANT_COLLECTION=mentor_profiles",
                    ]
                ),
                encoding="utf-8",
            )
            original_key = os.environ.get("UPSTAGE_API_KEY")
            original_qdrant_url = os.environ.get("QDRANT_URL")
            original_collection = os.environ.get("QDRANT_COLLECTION")
            os.environ["UPSTAGE_API_KEY"] = "up_existing"
            os.environ.pop("QDRANT_URL", None)
            os.environ.pop("QDRANT_COLLECTION", None)
            try:
                load_dotenv(env_path)

                self.assertEqual(os.environ["UPSTAGE_API_KEY"], "up_existing")
                self.assertEqual(os.environ["QDRANT_URL"], "http://localhost:6333")
                self.assertEqual(os.environ["QDRANT_COLLECTION"], "mentor_profiles")
            finally:
                _restore_env("UPSTAGE_API_KEY", original_key)
                _restore_env("QDRANT_URL", original_qdrant_url)
                _restore_env("QDRANT_COLLECTION", original_collection)

    def test_clients_can_read_settings_from_env_file(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "UPSTAGE_API_KEY=up_from_file",
                        "QDRANT_URL=http://localhost:6333",
                        "QDRANT_COLLECTION=mentor_profiles",
                    ]
                ),
                encoding="utf-8",
            )
            original_key = os.environ.get("UPSTAGE_API_KEY")
            original_qdrant_url = os.environ.get("QDRANT_URL")
            original_collection = os.environ.get("QDRANT_COLLECTION")
            os.environ.pop("UPSTAGE_API_KEY", None)
            os.environ.pop("QDRANT_URL", None)
            os.environ.pop("QDRANT_COLLECTION", None)
            try:
                embedding_client = UpstageEmbeddingClient.from_env(env_path=env_path)
                vector_store = QdrantMentorVectorStore.from_env(env_path=env_path)

                self.assertEqual(embedding_client.api_key, "up_from_file")
                self.assertEqual(vector_store.url, "http://localhost:6333")
                self.assertEqual(vector_store.collection_name, "mentor_profiles")
            finally:
                _restore_env("UPSTAGE_API_KEY", original_key)
                _restore_env("QDRANT_URL", original_qdrant_url)
                _restore_env("QDRANT_COLLECTION", original_collection)

    def test_mentor_document_contains_searchable_profile_fields(self):
        mentor = {
            "name": "이채린",
            "domain": ["AI", "LLM"],
            "keywords": ["rag", "langgraph"],
            "can_help": ["RAG 설계"],
            "profile_summary": "LLM 애플리케이션과 평가 설계에 강한 멘토",
        }

        document = mentor_to_document(mentor)

        self.assertIn("이름: 이채린", document)
        self.assertIn("분야: AI, LLM", document)
        self.assertIn("키워드: rag, langgraph", document)
        self.assertIn("도움 가능 영역: RAG 설계", document)
        self.assertIn("프로필: LLM 애플리케이션", document)

    def test_rag_retrieval_uses_query_embedding_and_vector_search(self):
        embedding_client = FakeEmbeddingClient()
        vector_store = FakeVectorStore()

        result = retrieve_mentor_candidates_rag(
            RAG_GAP_CONTEXT,
            embedding_client=embedding_client,
            vector_store=vector_store,
            limit=3,
        )

        self.assertEqual(embedding_client.queries, [build_search_query(RAG_GAP_CONTEXT)])
        self.assertEqual(vector_store.searches, [([1.0, 0.0, 0.0], 3)])
        self.assertEqual(result[0]["name"], "이채린")
        self.assertEqual(result[0]["retrieval_score"], 0.91)
        self.assertEqual(result[0]["matched_fields"], ["mentor_document"])
        self.assertIn("rag", result[0]["matched_keywords"])

    def test_rag_retrieval_prefers_refined_query_when_available(self):
        embedding_client = FakeEmbeddingClient()
        vector_store = FakeVectorStore()

        retrieve_mentor_candidates_rag(
            RAG_GAP_CONTEXT,
            embedding_client=embedding_client,
            vector_store=vector_store,
            refined_query="LangGraph RAG 평가 멘토",
        )

        self.assertEqual(embedding_client.queries, ["LangGraph RAG 평가 멘토"])

    def test_upstage_embedding_client_uses_query_and_passage_models(self):
        transport = FakeUpstageTransport()
        client = UpstageEmbeddingClient(api_key="up_test", post_json=transport)

        self.assertEqual(client.embed_query("RAG 멘토"), [0.1, 0.2, 0.3])
        self.assertEqual(client.embed_passages(["멘토 프로필"]), [[0.1, 0.2, 0.3]])

        query_payload = transport.calls[0][2]
        passage_payload = transport.calls[1][2]
        self.assertEqual(query_payload["model"], "solar-embedding-1-large-query")
        self.assertEqual(passage_payload["model"], "solar-embedding-1-large-passage")

    def test_qdrant_store_creates_collection_upserts_and_searches(self):
        transport = FakeQdrantTransport()
        store = QdrantMentorVectorStore(
            url="http://localhost:6333",
            collection_name="mentor_profiles",
            request_json=transport,
        )
        mentor = {
            "name": "서지훈",
            "domain": ["MLOps", "Infra"],
            "keywords": ["deployment"],
            "can_help": ["모델 서빙 구조 설계"],
            "less_relevant_for": [],
            "profile_summary": "MLOps 멘토",
        }

        store.ensure_collection(vector_size=4096)
        store.upsert_mentors([mentor], [[0.1, 0.2, 0.3]])
        results = store.search([0.1, 0.2, 0.3], limit=1)

        self.assertEqual(transport.calls[0][0], "PUT")
        self.assertIn("/collections/mentor_profiles", transport.calls[0][1])
        self.assertEqual(transport.calls[0][3]["vectors"]["size"], 4096)
        self.assertEqual(transport.calls[1][0], "PUT")
        self.assertIn("/points", transport.calls[1][1])
        self.assertEqual(transport.calls[2][0], "POST")
        self.assertIn("/points/search", transport.calls[2][1])
        self.assertEqual(results[0]["payload"]["name"], "서지훈")

    def test_index_mentors_embeds_documents_and_upserts_vectors(self):
        with TemporaryDirectory() as temp_dir:
            mentors_path = Path(temp_dir) / "mentors.json"
            mentors_path.write_text(
                """
                [
                  {
                    "name": "이채린",
                    "domain": ["AI", "LLM"],
                    "keywords": ["rag"],
                    "can_help": ["RAG 설계"],
                    "less_relevant_for": [],
                    "profile_summary": "LLM 멘토"
                  }
                ]
                """,
                encoding="utf-8",
            )
            embedding_client = FakeEmbeddingClient()
            vector_store = FakeVectorStore()

            count = index_mentors(
                mentors_path=mentors_path,
                embedding_client=embedding_client,
                vector_store=vector_store,
            )

        self.assertEqual(count, 1)
        self.assertEqual(vector_store.collection_sizes, [4096])
        self.assertEqual(len(embedding_client.passages[0]), 1)
        self.assertIn("이름: 이채린", embedding_client.passages[0][0])
        self.assertEqual(vector_store.upserts[0][0][0]["name"], "이채린")
        self.assertEqual(vector_store.upserts[0][1], [[1.0, 0.0, 0.0]])

    def test_index_mentors_rejects_embedding_count_mismatch(self):
        with TemporaryDirectory() as temp_dir:
            mentors_path = Path(temp_dir) / "mentors.json"
            mentors_path.write_text(
                """
                [
                  {
                    "name": "이채린",
                    "domain": ["AI", "LLM"],
                    "keywords": ["rag"],
                    "can_help": ["RAG 설계"],
                    "less_relevant_for": [],
                    "profile_summary": "LLM 멘토"
                  }
                ]
                """,
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                index_mentors(
                    mentors_path=mentors_path,
                    embedding_client=MismatchedEmbeddingClient(),
                    vector_store=FakeVectorStore(),
                )


if __name__ == "__main__":
    unittest.main()

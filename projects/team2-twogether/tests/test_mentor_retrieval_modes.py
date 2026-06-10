import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.app.nodes.mentor_retrieval import (
    get_retrieval_mode,
    merge_hybrid_candidates,
    mentor_retrieval_node,
)


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


class ExplodingEmbeddingClient:
    def embed_query(self, text):
        raise AssertionError("Vector embedding should not be called in bm25 mode.")


class ExplodingVectorStore:
    def search(self, query_vector, limit):
        raise AssertionError("Vector store should not be called in bm25 mode.")


class FakeEmbeddingClient:
    def __init__(self, should_fail=False):
        self.queries = []
        self.should_fail = should_fail

    def embed_query(self, text):
        if self.should_fail:
            raise OSError("simulated vector failure")
        self.queries.append(text)
        return [1.0, 0.0, 0.0]


class FakeVectorStore:
    def __init__(self, results=None):
        self.searches = []
        self.results = results or [
            {
                "score": 0.91,
                "payload": {
                    "mentor_id": "mock_007",
                    "name": "이채린",
                    "domain": ["AI", "LLM"],
                    "keywords": ["rag", "evaluation", "langgraph"],
                    "can_help": ["RAG 설계", "LLM 평가 방법"],
                    "less_relevant_for": ["세일즈"],
                    "profile_summary": "LLM 애플리케이션과 평가 설계에 강한 멘토",
                },
            }
        ]

    def search(self, query_vector, limit):
        self.searches.append((query_vector, limit))
        return self.results


class MentorRetrievalModesTest(unittest.TestCase):
    def test_default_mode_is_bm25_without_env(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            original_mode = os.environ.get("MENTOR_RETRIEVAL_MODE")
            os.environ.pop("MENTOR_RETRIEVAL_MODE", None)
            try:
                self.assertEqual(get_retrieval_mode(env_path), "bm25")
            finally:
                _restore_env("MENTOR_RETRIEVAL_MODE", original_mode)

    def test_bm25_mode_does_not_call_vector_clients(self):
        result = mentor_retrieval_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieval_mode": "bm25",
                "_embedding_client": ExplodingEmbeddingClient(),
                "_vector_store": ExplodingVectorStore(),
            }
        )

        self.assertEqual(result["retrieved_mentors"][0]["name"], "이채린")
        self.assertEqual(result["retrieved_mentors"][0]["retrieval_source"], "bm25_rule")

    def test_api_env_without_mode_still_uses_bm25(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "UPSTAGE_API_KEY=up_from_file",
                        "QDRANT_URL=http://localhost:6333",
                    ]
                ),
                encoding="utf-8",
            )
            original_values = {
                name: os.environ.get(name)
                for name in ("MENTOR_RETRIEVAL_MODE", "UPSTAGE_API_KEY", "QDRANT_URL")
            }
            for name in original_values:
                os.environ.pop(name, None)
            try:
                result = mentor_retrieval_node(
                    {
                        "gap_context": RAG_GAP_CONTEXT,
                        "_env_path": env_path,
                        "_embedding_client": ExplodingEmbeddingClient(),
                        "_vector_store": ExplodingVectorStore(),
                    }
                )
            finally:
                for name, value in original_values.items():
                    _restore_env(name, value)

            self.assertEqual(result["retrieved_mentors"][0]["name"], "이채린")
            self.assertEqual(
                result["retrieved_mentors"][0]["retrieval_source"],
                "bm25_rule",
            )

    def test_vector_mode_uses_fake_vector_store(self):
        embedding_client = FakeEmbeddingClient()
        vector_store = FakeVectorStore()

        result = mentor_retrieval_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieval_mode": "vector",
                "_embedding_client": embedding_client,
                "_vector_store": vector_store,
            }
        )

        self.assertEqual(len(embedding_client.queries), 1)
        self.assertEqual(vector_store.searches, [([1.0, 0.0, 0.0], 5)])
        self.assertEqual(result["retrieved_mentors"][0]["retrieval_source"], "vector")

    def test_vector_failure_falls_back_to_bm25(self):
        result = mentor_retrieval_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieval_mode": "vector",
                "_embedding_client": FakeEmbeddingClient(should_fail=True),
                "_vector_store": FakeVectorStore(),
            }
        )

        self.assertEqual(result["retrieved_mentors"][0]["name"], "이채린")
        self.assertEqual(result["retrieved_mentors"][0]["retrieval_source"], "bm25_rule")

    def test_hybrid_mode_merges_and_dedupes_candidates(self):
        embedding_client = FakeEmbeddingClient()
        vector_store = FakeVectorStore()

        result = mentor_retrieval_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieval_mode": "hybrid",
                "_embedding_client": embedding_client,
                "_vector_store": vector_store,
            }
        )

        candidates = result["retrieved_mentors"]
        names = [candidate["name"] for candidate in candidates]
        self.assertEqual(names.count("이채린"), 1)
        self.assertEqual(candidates[0]["name"], "이채린")
        self.assertEqual(candidates[0]["retrieval_source"], "hybrid")
        self.assertIn("mentor_document", candidates[0]["matched_fields"])
        self.assertGreaterEqual(candidates[0]["retrieval_score"], 0)
        self.assertLessEqual(candidates[0]["retrieval_score"], 1)

    def test_hybrid_vector_failure_falls_back_to_bm25(self):
        result = mentor_retrieval_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieval_mode": "hybrid",
                "_embedding_client": FakeEmbeddingClient(should_fail=True),
                "_vector_store": FakeVectorStore(),
            }
        )

        self.assertEqual(result["retrieved_mentors"][0]["name"], "이채린")
        self.assertEqual(result["retrieved_mentors"][0]["retrieval_source"], "bm25_rule")

    def test_hybrid_score_uses_weighted_normalized_scores(self):
        candidates = merge_hybrid_candidates(
            [
                {
                    "name": "A",
                    "retrieval_score": 10,
                    "matched_keywords": ["rag"],
                    "matched_fields": ["keywords"],
                },
                {
                    "name": "B",
                    "retrieval_score": 5,
                    "matched_keywords": ["mlops"],
                    "matched_fields": ["keywords"],
                },
            ],
            [
                {
                    "name": "A",
                    "retrieval_score": 0.2,
                    "matched_keywords": ["langgraph"],
                    "matched_fields": ["mentor_document"],
                },
                {
                    "name": "C",
                    "retrieval_score": 0.4,
                    "matched_keywords": ["evaluation"],
                    "matched_fields": ["mentor_document"],
                },
            ],
            limit=3,
        )

        self.assertEqual([candidate["name"] for candidate in candidates], ["A", "C", "B"])
        self.assertEqual(candidates[0]["retrieval_score"], 0.725)
        self.assertEqual(candidates[1]["retrieval_score"], 0.55)
        self.assertEqual(candidates[2]["retrieval_score"], 0.225)
        self.assertEqual(candidates[0]["retrieval_source"], "hybrid")

    def test_hybrid_keeps_anonymous_candidates_separate(self):
        candidates = merge_hybrid_candidates(
            [
                {"retrieval_score": 1.0, "matched_keywords": [], "matched_fields": []},
                {"retrieval_score": 0.8, "matched_keywords": [], "matched_fields": []},
            ],
            [],
            limit=5,
        )

        self.assertEqual(len(candidates), 2)


def _restore_env(name, value):
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()

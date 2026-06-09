import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from backend.app.nodes.mentor_retrieval import (
    build_search_query,
    load_mentors,
    mentor_retrieval_node,
    retrieve_mentor_candidates,
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
    "query_hints": [
        "RAG",
        "retrieval quality",
        "embedding",
        "mentor recommendation",
        "LLM evaluation",
        "LangGraph",
    ],
    "source_fields": ["concerns", "tech_stack", "constraints"],
}


INFRA_GAP_CONTEXT = {
    "main_gap": "Infra, MLOps 영역의 배포 구조 설계 역량 부족",
    "gap_categories": ["Infra", "MLOps", "DevOps"],
    "needed_mentor_expertise": ["배포 구조 설계", "모델 서빙", "운영 환경 구성"],
    "priority": "high",
    "reason": "배포와 운영 경험 부족이 현재 데모 완성도의 주요 위험입니다.",
    "query_hints": ["deployment", "MLOps", "Docker", "model serving"],
    "source_fields": ["concerns", "constraints", "tech_stack"],
}


class MentorRetrievalTest(unittest.TestCase):
    def test_default_mock_mentor_data_has_twenty_entries(self):
        self.assertEqual(len(load_mentors()), 20)

    def test_default_mentor_data_has_unique_ids_and_required_fields(self):
        mentors = load_mentors()
        required_fields = {
            "mentor_id",
            "name",
            "domain",
            "keywords",
            "can_help",
            "less_relevant_for",
            "profile_summary",
        }

        self.assertEqual(
            len({mentor["mentor_id"] for mentor in mentors}),
            len(mentors),
        )
        for mentor in mentors:
            self.assertTrue(required_fields.issubset(mentor))
            self.assertTrue(mentor["domain"])
            self.assertTrue(mentor["keywords"])
            self.assertTrue(mentor["can_help"])

    def test_rag_langgraph_gap_retrieves_ai_llm_mentor_first(self):
        mentors = load_mentors()

        candidates = retrieve_mentor_candidates(RAG_GAP_CONTEXT, mentors, limit=3)

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name"], "이채린")
        self.assertIn("rag", candidates[0]["matched_keywords"])
        self.assertIn("langgraph", candidates[0]["matched_keywords"])
        self.assertEqual(candidates[0]["retrieval_source"], "bm25_rule")
        self.assertGreater(candidates[0]["retrieval_score"], 0)

    def test_infra_gap_retrieves_deployment_mentor_first(self):
        mentors = load_mentors()

        candidates = retrieve_mentor_candidates(INFRA_GAP_CONTEXT, mentors, limit=3)

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name"], "서지훈")
        self.assertIn("deployment", candidates[0]["matched_keywords"])
        self.assertIn("keywords", candidates[0]["matched_fields"])

    def test_build_search_query_uses_query_hints_and_expertise(self):
        query = build_search_query(RAG_GAP_CONTEXT)

        self.assertIn("RAG", query)
        self.assertIn("LangGraph", query)
        self.assertIn("RAG 검색 구조 설계", query)
        self.assertIn("LLM evaluation", query)

    def test_node_without_gap_context_returns_empty_result(self):
        result = mentor_retrieval_node({})

        self.assertEqual(result, {"search_query": "", "retrieved_mentors": []})

    def test_empty_mentor_data_returns_empty_candidates(self):
        candidates = retrieve_mentor_candidates(RAG_GAP_CONTEXT, [], limit=3)

        self.assertEqual(candidates, [])

    def test_load_mentors_handles_empty_file(self):
        with TemporaryDirectory() as temp_dir:
            empty_file = Path(temp_dir) / "empty_mentors.json"
            empty_file.write_text("", encoding="utf-8")

            self.assertEqual(load_mentors(empty_file), [])


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.app.nodes.mentor_retrieval import load_mentors
from backend.app.rag.bm25_retriever import retrieve_bm25_rule_candidates


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


INFRA_GAP_CONTEXT = {
    "main_gap": "Infra, MLOps 영역의 배포 구조 설계 역량 부족",
    "gap_categories": ["Infra", "MLOps", "DevOps"],
    "needed_mentor_expertise": ["배포 구조 설계", "모델 서빙", "운영 환경 구성"],
    "priority": "high",
    "reason": "배포와 운영 경험 부족이 현재 데모 완성도의 주요 위험입니다.",
    "query_hints": ["deployment", "MLOps", "Docker", "model serving"],
    "source_fields": ["concerns", "constraints", "tech_stack"],
}


class Bm25RetrieverTest(unittest.TestCase):
    def test_rag_langgraph_gap_retrieves_ai_llm_mentor_first(self):
        candidates = retrieve_bm25_rule_candidates(
            RAG_GAP_CONTEXT,
            load_mentors(),
            limit=3,
        )

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name"], "이채린")
        self.assertEqual(candidates[0]["retrieval_source"], "bm25_rule")
        self.assertIn("rag", candidates[0]["matched_keywords"])
        self.assertIn("keywords", candidates[0]["matched_fields"])
        self.assertGreater(candidates[0]["retrieval_score"], 0)

    def test_infra_gap_retrieves_deployment_mentor_first(self):
        candidates = retrieve_bm25_rule_candidates(
            INFRA_GAP_CONTEXT,
            load_mentors(),
            limit=3,
        )

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name"], "서지훈")
        self.assertIn("deployment", candidates[0]["matched_keywords"])
        self.assertEqual(candidates[0]["retrieval_source"], "bm25_rule")

    def test_empty_mentor_data_returns_empty_candidates(self):
        self.assertEqual(retrieve_bm25_rule_candidates(RAG_GAP_CONTEXT, []), [])


if __name__ == "__main__":
    unittest.main()

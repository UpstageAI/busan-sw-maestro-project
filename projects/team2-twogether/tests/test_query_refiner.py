import unittest

from backend.app.nodes.mentor_retrieval import build_search_query
from backend.app.nodes.query_refiner import query_refiner_node, refine_search_query
from backend.app.rag.bm25_retriever import tokenize


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
    "query_hints": ["RAG", "retrieval quality", "embedding", "LangGraph"],
    "source_fields": ["concerns"],
}


class QueryRefinerTest(unittest.TestCase):
    def test_refined_query_appends_unused_terms(self):
        # A minimal base query that omits most gap signals.
        base_query = "RAG"

        refined = refine_search_query(RAG_GAP_CONTEXT, base_query, [])

        self.assertIn("RAG", refined)
        self.assertNotEqual(refined, base_query)
        refined_tokens = set(tokenize(refined))
        # An expertise term that was not in the base query should now appear.
        self.assertTrue(set(tokenize("LangGraph")).issubset(refined_tokens))
        self.assertTrue(set(tokenize("embedding")).issubset(refined_tokens))

    def test_node_increments_retry_count_and_sets_query(self):
        result = query_refiner_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "search_query": "RAG",
                "retry_count": 0,
            }
        )

        self.assertEqual(result["retry_count"], 1)
        self.assertIn("refined_query", result)
        self.assertTrue(result["refined_query"])

    def test_node_defaults_retry_count_when_absent(self):
        result = query_refiner_node(
            {"gap_context": RAG_GAP_CONTEXT, "search_query": "RAG"}
        )

        self.assertEqual(result["retry_count"], 1)

    def test_falls_back_to_built_query_when_no_search_query(self):
        refined = refine_search_query(RAG_GAP_CONTEXT, "", [])

        # Without a base query it should at least reproduce the built query terms.
        built_tokens = set(tokenize(build_search_query(RAG_GAP_CONTEXT)))
        self.assertTrue(built_tokens.issubset(set(tokenize(refined))))

    def test_empty_gap_context_returns_base_query_safely(self):
        self.assertEqual(refine_search_query({}, "RAG retrieval", []), "RAG retrieval")
        self.assertEqual(refine_search_query({}, "", []), "")

    def test_no_unused_terms_returns_base_query(self):
        full_query = build_search_query(RAG_GAP_CONTEXT)

        refined = refine_search_query(RAG_GAP_CONTEXT, full_query, [])

        # Every gap term is already present, so the query is unchanged.
        self.assertEqual(set(tokenize(refined)), set(tokenize(full_query)))


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.app.nodes.fit_evaluation import (
    CONFIDENCE_THRESHOLD,
    evaluate_mentor_fit,
    fit_evaluation_node,
)
from backend.app.nodes.mentor_retrieval import load_mentors, retrieve_mentor_candidates


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


IRRELEVANT_GAP_CONTEXT = {
    "main_gap": "베이킹 역량 부족",
    "gap_categories": ["요리"],
    "needed_mentor_expertise": ["베이킹 기술"],
    "priority": "low",
    "reason": "프로젝트와 무관한 요청.",
    "query_hints": ["cooking", "baking", "patisserie"],
    "source_fields": ["concerns"],
}


def _candidates(gap_context, limit=5):
    return retrieve_mentor_candidates(gap_context, load_mentors(), limit=limit)


class FitEvaluationTest(unittest.TestCase):
    def test_high_fit_mentor_scores_higher_and_results_sorted(self):
        candidates = _candidates(RAG_GAP_CONTEXT)

        evaluated = evaluate_mentor_fit(RAG_GAP_CONTEXT, candidates)

        self.assertGreaterEqual(len(evaluated), 2)
        # 이채린 (rag, langgraph, evaluation) is the strongest RAG match.
        self.assertEqual(evaluated[0]["name"], "이채린")
        scores = [mentor["score"] for mentor in evaluated]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertGreater(evaluated[0]["score"], evaluated[-1]["score"])

    def test_scores_within_zero_to_hundred(self):
        evaluated = evaluate_mentor_fit(RAG_GAP_CONTEXT, _candidates(RAG_GAP_CONTEXT))

        for mentor in evaluated:
            self.assertGreaterEqual(mentor["score"], 0.0)
            self.assertLessEqual(mentor["score"], 100.0)

    def test_reason_only_uses_strings_present_in_data(self):
        evaluated = evaluate_mentor_fit(RAG_GAP_CONTEXT, _candidates(RAG_GAP_CONTEXT))

        gap_terms = {
            *RAG_GAP_CONTEXT["gap_categories"],
            *RAG_GAP_CONTEXT["needed_mentor_expertise"],
        }
        for mentor in evaluated:
            reason = mentor["reason"]
            self.assertTrue(reason)
            # Reason must be grounded: either it cites a gap term plus a mentor
            # string that actually exists in the mentor's data, or it falls back
            # to the verbatim profile_summary.
            mentor_corpus = " ".join(
                [
                    *mentor.get("matched_keywords", []),
                    *mentor.get("can_help", []),
                    str(mentor.get("profile_summary", "")),
                ]
            ).casefold()
            if reason == mentor.get("profile_summary"):
                continue
            self.assertTrue(
                any(term in reason for term in gap_terms),
                f"reason missing gap evidence: {reason}",
            )
            # The quoted mentor evidence is wrapped in single quotes.
            quoted = reason.split("'")
            self.assertGreaterEqual(len(quoted), 3, reason)
            mentor_evidence = quoted[1]
            self.assertIn(mentor_evidence.casefold(), mentor_corpus)

    def test_confident_for_strong_match(self):
        result = fit_evaluation_node(
            {
                "gap_context": RAG_GAP_CONTEXT,
                "retrieved_mentors": _candidates(RAG_GAP_CONTEXT),
            }
        )

        self.assertTrue(result["is_recommendation_confident"])
        self.assertGreaterEqual(
            max(m["score"] for m in result["evaluated_mentors"]),
            CONFIDENCE_THRESHOLD,
        )

    def test_irrelevant_gap_yields_no_candidates_and_low_confidence(self):
        candidates = _candidates(IRRELEVANT_GAP_CONTEXT)
        self.assertEqual(candidates, [])

        result = fit_evaluation_node(
            {
                "gap_context": IRRELEVANT_GAP_CONTEXT,
                "retrieved_mentors": candidates,
            }
        )

        self.assertEqual(result["evaluated_mentors"], [])
        self.assertFalse(result["is_recommendation_confident"])

    def test_node_without_inputs_returns_empty(self):
        self.assertEqual(
            fit_evaluation_node({}),
            {"evaluated_mentors": [], "is_recommendation_confident": False},
        )

    def test_output_shape_matches_recommendation_keys(self):
        evaluated = evaluate_mentor_fit(RAG_GAP_CONTEXT, _candidates(RAG_GAP_CONTEXT))

        for key in ("name", "domain", "score", "reason", "matched_keywords"):
            self.assertIn(key, evaluated[0])
        self.assertIsInstance(evaluated[0]["domain"], list)
        self.assertIsInstance(evaluated[0]["score"], float)


if __name__ == "__main__":
    unittest.main()

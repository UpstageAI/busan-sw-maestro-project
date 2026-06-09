import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import summarizer


class SummarizerTest(unittest.TestCase):
    def test_empty_results_return_no_risk_summary_without_llm(self):
        with patch.object(summarizer, "_summarize_with_llm") as mock_llm:
            result = summarizer.summarize([])

        self.assertEqual(result, summarizer._NO_RISK_SUMMARY)
        mock_llm.assert_not_called()

    def test_results_without_risky_clause_return_no_risk_summary(self):
        results = [
            {
                "clause": "계약 기간은 1년입니다.",
                "is_risky": False,
                "reason": "일반적인 계약 기간입니다.",
                "risk_level": "low",
            }
        ]

        self.assertEqual(summarizer.summarize(results), summarizer._NO_RISK_SUMMARY)

    def test_high_risk_clause_returns_high_fallback(self):
        results = [
            {
                "clause": "계약 위반 시 보증금을 반환하지 않는다.",
                "is_risky": True,
                "reason": "보증금 반환이 제한될 수 있습니다.",
                "risk_level": "high",
            }
        ]

        with patch.dict(os.environ, {}, clear=True):
            result = summarizer.summarize(results)

        self.assertIn("전체 위험 수준은 높음", result)
        self.assertIn("높은 위험 조항이 포함되어 있어", result)

    def test_medium_only_clause_returns_medium_fallback(self):
        results = [
            {
                "clause": "검수 완료 후 대금을 지급한다.",
                "is_risky": True,
                "reason": "검수 기준과 지급 기한이 명확하지 않습니다.",
                "risk_level": "medium",
            }
        ]

        with patch.dict(os.environ, {}, clear=True):
            result = summarizer.summarize(results)

        self.assertIn("전체 위험 수준은 중간", result)
        self.assertIn("일부 조항에서 주의가 필요한 요소가 확인되었습니다.", result)

    def test_missing_fields_and_invalid_items_do_not_raise(self):
        results = [
            {"is_risky": True},
            {"clause": "필드가 누락된 비위험 조항"},
            None,
            "invalid item",
        ]

        with patch.dict(os.environ, {}, clear=True):
            result = summarizer.summarize(results)

        self.assertIsInstance(result, str)
        self.assertIn("전체 위험 수준은 중간", result)

    def test_missing_api_key_returns_fallback_without_creating_llm(self):
        results = [
            {
                "clause": "자동으로 계약이 갱신된다.",
                "is_risky": True,
                "reason": "자동 갱신 해지 조건을 확인해야 합니다.",
                "risk_level": "low",
            }
        ]

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(summarizer, "ChatOpenAI") as mock_chat_openai:
                result = summarizer.summarize(results)

        self.assertIn("큰 위험은 낮지만 세부 조건 확인이 필요합니다.", result)
        mock_chat_openai.assert_not_called()

    def test_llm_failure_returns_fallback(self):
        results = [
            {
                "clause": "계약 위반 시 위약금을 지급한다.",
                "is_risky": True,
                "reason": "위약금 범위가 명확하지 않습니다.",
                "risk_level": "high",
            }
        ]

        with patch.dict(
            os.environ, {"UPSTAGE_API_KEY": "test-api-key"}, clear=True
        ):
            with patch.object(
                summarizer,
                "_summarize_with_llm",
                side_effect=RuntimeError("LLM request failed"),
            ):
                result = summarizer.summarize(results)

        self.assertIn("높은 위험 조항이 포함되어 있어", result)

    def test_summary_input_is_sorted_and_long_clause_is_truncated(self):
        long_clause = "가" * 501
        results = [
            {"risk_level": "low", "clause": long_clause, "reason": "낮은 위험"},
            {"risk_level": "high", "clause": "고위험 조항", "reason": "높은 위험"},
        ]

        summary_input = summarizer._build_summary_input(results)

        self.assertLess(summary_input.index("HIGH"), summary_input.index("LOW"))
        self.assertIn(f"{'가' * 500}...", summary_input)
        self.assertNotIn("가" * 501, summary_input)


if __name__ == "__main__":
    unittest.main()

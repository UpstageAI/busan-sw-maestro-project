import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import analyzer, classifier, explainer


class ServiceFallbackTest(unittest.TestCase):
    def test_detect_contract_type_without_api_key_uses_rules(self):
        text = "본 용역 계약은 산출물 검수 후 대금을 지급하는 외주 계약이다."
        with patch.dict(os.environ, {}, clear=True):
            result = analyzer.detect_contract_type(text)

        self.assertEqual(result, "외주")

    def test_analyze_clauses_without_api_key_has_stable_fields(self):
        with patch.dict(os.environ, {}, clear=True):
            result = analyzer.analyze_clauses(
                ["계약 위반 시 위약금을 지급한다."],
                "기타",
            )

        self.assertEqual(set(result[0]), {"clause", "is_risky", "reason"})
        self.assertTrue(result[0]["is_risky"])

    def test_classifier_handles_missing_fields(self):
        result = classifier.classify_risk(
            [{"clause": "일반 조항"}, {"is_risky": True}, None],
            "기타",
        )

        self.assertEqual(result[0]["risk_level"], "low")
        self.assertEqual(result[1]["risk_level"], "medium")
        self.assertEqual(len(result), 2)

    def test_explainer_without_api_key_returns_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            result = explainer.explain("계약은 1년간 유지된다.")

        self.assertIn("현재 상세 AI 설명을 사용할 수 없어", result)


if __name__ == "__main__":
    unittest.main()

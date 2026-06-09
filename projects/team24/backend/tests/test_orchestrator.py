import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import orchestrator


class OrchestratorTest(unittest.TestCase):
    def test_risky_clause_runs_classification_and_summary(self):
        analysis = [
            {
                "clause": "제1조 위약금을 지급한다.",
                "is_risky": True,
                "reason": "위약금 조건을 확인해야 합니다.",
            }
        ]
        classified = [{**analysis[0], "risk_level": "high"}]

        with (
            patch.object(orchestrator, "extract_text", return_value="계약서 본문"),
            patch.object(orchestrator, "split_clauses", return_value=["제1조 조항"]),
            patch.object(orchestrator, "analyze_clauses", return_value=analysis),
            patch.object(
                orchestrator,
                "classify_risk",
                return_value=classified,
            ) as mock_classify,
            patch.object(
                orchestrator,
                "summarize",
                return_value="위험 요약",
            ) as mock_summarize,
        ):
            result = orchestrator.run_analysis_pipeline(
                b"contract",
                "contract.txt",
                "외주",
            )

        self.assertEqual(result["contract_type"], "외주")
        self.assertEqual(result["clauses"], classified)
        self.assertEqual(result["summary"], "위험 요약")
        mock_classify.assert_called_once()
        mock_summarize.assert_called_once()
        steps = [log["step"] for log in result["process_logs"]]
        self.assertIn("has_risky_clause", steps)
        self.assertIn("classify_risk", steps)
        self.assertIn("summarize", steps)

    def test_safe_clause_skips_classification_and_summary(self):
        analysis = [
            {
                "clause": "제1조 계약 기간은 1년입니다.",
                "is_risky": False,
                "reason": "위험 요소가 없습니다.",
            }
        ]

        with (
            patch.object(orchestrator, "extract_text", return_value="계약서 본문"),
            patch.object(orchestrator, "split_clauses", return_value=["제1조 조항"]),
            patch.object(orchestrator, "analyze_clauses", return_value=analysis),
            patch.object(orchestrator, "classify_risk") as mock_classify,
            patch.object(orchestrator, "summarize") as mock_summarize,
        ):
            result = orchestrator.run_analysis_pipeline(
                b"contract",
                "contract.txt",
                "근로",
            )

        self.assertEqual(result["clauses"][0]["risk_level"], "low")
        self.assertFalse(result["clauses"][0]["is_risky"])
        mock_classify.assert_not_called()
        mock_summarize.assert_not_called()
        steps = [log["step"] for log in result["process_logs"]]
        self.assertIn("has_risky_clause", steps)
        self.assertIn("build_safe_result", steps)
        self.assertNotIn("classify_risk", steps)
        self.assertNotIn("summarize", steps)

    def test_auto_detection_is_returned(self):
        with (
            patch.object(orchestrator, "extract_text", return_value="외주 계약서"),
            patch.object(
                orchestrator,
                "detect_contract_type",
                return_value="외주",
            ) as mock_detect,
            patch.object(orchestrator, "split_clauses", return_value=["제1조 조항"]),
            patch.object(
                orchestrator,
                "analyze_clauses",
                return_value=[
                    {
                        "clause": "제1조 조항",
                        "is_risky": False,
                        "reason": "위험 없음",
                    }
                ],
            ),
        ):
            result = orchestrator.run_analysis_pipeline(
                b"contract",
                "contract.txt",
                "자동 감지",
            )

        self.assertEqual(result["contract_type"], "외주")
        self.assertEqual(result["detected_type"], "외주")
        mock_detect.assert_called_once_with("외주 계약서")

    def test_failure_contains_failed_step_log(self):
        with patch.object(
            orchestrator,
            "extract_text",
            side_effect=ValueError("텍스트 추출 실패"),
        ):
            with self.assertRaises(orchestrator.AnalysisPipelineError) as context:
                orchestrator.run_analysis_pipeline(
                    b"contract",
                    "contract.txt",
                    "기타",
                )

        error = context.exception
        self.assertEqual(error.step, "extract_text")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.process_logs[-1]["status"], "failed")

    def test_stream_events_include_started_finished_skipped_and_completed(self):
        analysis = [
            {
                "clause": "제1조 계약 기간은 1년입니다.",
                "is_risky": False,
                "reason": "위험 요소가 없습니다.",
            }
        ]

        with (
            patch.object(orchestrator, "extract_text", return_value="계약서 본문"),
            patch.object(orchestrator, "split_clauses", return_value=["제1조 조항"]),
            patch.object(orchestrator, "analyze_clauses", return_value=analysis),
            patch.object(orchestrator, "classify_risk") as mock_classify,
            patch.object(orchestrator, "summarize") as mock_summarize,
        ):
            events = list(
                orchestrator.iter_analysis_pipeline_events(
                    b"contract",
                    "contract.txt",
                    "근로",
                )
            )

        event_names = [event["event"] for event in events]
        self.assertIn("step_started", event_names)
        self.assertIn("step_finished", event_names)
        self.assertIn("step_skipped", event_names)
        self.assertEqual(events[-1]["event"], "completed")
        self.assertEqual(
            [
                event["step"]
                for event in events
                if event["event"] == "step_skipped"
            ],
            ["classify_risk", "summarize"],
        )
        mock_classify.assert_not_called()
        mock_summarize.assert_not_called()

if __name__ == "__main__":
    unittest.main()

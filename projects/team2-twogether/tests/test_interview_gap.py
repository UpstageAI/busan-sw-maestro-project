import unittest

from backend.app.nodes.interview_gap import analyze_project_gap, interview_gap_node


class InterviewGapAnalyzerTest(unittest.TestCase):
    def setUp(self):
        self.valid_parsed_input = {
            "project_summary": "SW마에스트로 멘토 추천 Agentic RAG 서비스",
            "tech_stack": ["FastAPI", "LangGraph", "Upstage", "RAG", "Streamlit"],
            "current_stage": "초기 구현 단계",
            "concerns": ["RAG 검색 품질", "추천 근거 생성", "LangGraph 분기 설계"],
            "domain": ["AI", "Agent", "Recommendation"],
            "constraints": ["짧은 개발 기간", "로컬 데모 중심", "합성 멘토 데이터 사용"],
            "user_goal": "현재 프로젝트의 부족한 역량을 보완해줄 멘토 추천",
        }

    def test_mock_input_prioritizes_rag_from_first_concern(self):
        result = analyze_project_gap(self.valid_parsed_input)

        self.assertEqual(result.priority, "high")
        self.assertEqual(result.gap_categories[0], "RAG")
        self.assertIn("LLM Evaluation", result.gap_categories)
        self.assertIn("Agentic Workflow", result.gap_categories)
        self.assertIn("retrieval quality", result.query_hints)

    def test_infra_input_maps_to_deployment_expertise(self):
        result = analyze_project_gap(
            {
                "project_summary": "AI 모델 API 서비스",
                "tech_stack": ["FastAPI", "Docker"],
                "current_stage": "배포 준비 단계",
                "concerns": ["배포가 막막하다", "서버 운영 경험이 부족하다"],
                "domain": ["AI"],
                "constraints": ["짧은 개발 기간"],
                "user_goal": "운영 가능한 데모 배포",
            }
        )

        self.assertEqual(result.gap_categories[:3], ["Infra", "MLOps", "DevOps"])
        self.assertIn("배포 구조 설계", result.needed_mentor_expertise)
        self.assertIn("deployment", result.query_hints)

    def test_product_input_does_not_match_fastapi_as_api_gap(self):
        result = analyze_project_gap(
            {
                "project_summary": "학습자용 추천 서비스",
                "tech_stack": ["React", "FastAPI"],
                "current_stage": "기획 단계",
                "concerns": ["문제 정의가 모호하다", "사용자 검증이 필요하다"],
                "domain": ["Education"],
                "constraints": ["데모 전 사용자 인터뷰 필요"],
                "user_goal": "서비스 방향성 검증",
            }
        )

        self.assertEqual(result.gap_categories[:3], ["Product", "UX", "Research"])
        self.assertNotIn("Infra", result.gap_categories)
        self.assertNotIn("Architecture", result.gap_categories)
        self.assertIn("user validation", result.query_hints)

    def test_node_returns_gap_context_with_all_contract_fields(self):
        result = interview_gap_node({"parsed_input": self.valid_parsed_input})

        self.assertEqual(set(result.keys()), {"gap_context"})
        gap_context = result["gap_context"]
        self.assertEqual(
            set(gap_context.keys()),
            {
                "main_gap",
                "gap_categories",
                "needed_mentor_expertise",
                "priority",
                "reason",
                "query_hints",
                "source_fields",
            },
        )

    def test_node_does_not_create_gap_context_for_empty_parsed_input(self):
        self.assertEqual(
            interview_gap_node({"parsed_input": {}}),
            {"gap_context": None},
        )

    def test_node_does_not_create_gap_context_without_parsed_input(self):
        self.assertEqual(interview_gap_node({}), {"gap_context": None})

    def test_stage_constraints_and_concerns_feed_priority_reason_and_sources(self):
        result = interview_gap_node({"parsed_input": self.valid_parsed_input})
        gap_context = result["gap_context"]

        self.assertEqual(gap_context["priority"], "high")
        self.assertIn("현재 고민", gap_context["reason"])
        self.assertIn("진행 단계", gap_context["reason"])
        self.assertIn("제약 조건", gap_context["reason"])
        self.assertIn("RAG 검색 품질", gap_context["reason"])
        self.assertIn("초기 구현 단계", gap_context["reason"])
        self.assertIn("짧은 개발 기간", gap_context["reason"])
        self.assertIn("constraints", gap_context["source_fields"])
        self.assertIn("current_stage", gap_context["source_fields"])
        self.assertIn("concerns", gap_context["source_fields"])


if __name__ == "__main__":
    unittest.main()

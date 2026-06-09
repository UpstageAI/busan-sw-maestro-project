import unittest

from backend.app.llm.schemas import GapReview
from backend.app.nodes.interview_gap import (
    _review_gap_with_solar,
    analyze_project_gap,
    interview_gap_node,
)
from backend.app.schemas.gap import GapContext, ParsedInput


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

    def test_game_input_maps_to_game_mentoring(self):
        result = analyze_project_gap(
            {
                "project_summary": "RPG 게임을 만들고 싶다",
                "current_stage": "아이디어 단계",
                "concerns": ["게임 기획과 구현 방법을 모르겠다"],
                "user_goal": "작은 RPG 프로토타입 완성",
            }
        )

        self.assertEqual(result.gap_categories[0], "Game Development")
        self.assertIn("Game Design", result.gap_categories)
        self.assertIn("RPG", result.query_hints)

    def test_startup_input_maps_to_business_and_growth(self):
        result = analyze_project_gap(
            {
                "project_summary": "초기 창업 아이템",
                "current_stage": "아이디어 단계",
                "concerns": ["시장 검증과 수익 모델이 고민이다"],
                "user_goal": "사업 방향 검증",
            }
        )

        self.assertEqual(result.gap_categories[0], "Startup")
        self.assertIn("Business", result.gap_categories)
        self.assertIn("go-to-market", result.query_hints)


if __name__ == "__main__":
    unittest.main()


class FakeGapSolar:
    is_configured = True

    def __init__(self, gap_context=None, error=None):
        self.gap_context = gap_context
        self.error = error

    def complete_json(self, **kwargs):
        if self.error:
            raise self.error
        return GapReview(gap_context=self.gap_context)


class InspectingGapSolar(FakeGapSolar):
    def __init__(self, gap_context):
        super().__init__(gap_context)
        self.system_prompt = ""

    def complete_json(self, **kwargs):
        self.system_prompt = kwargs["system_prompt"]
        return super().complete_json(**kwargs)


def test_solar_can_review_rule_gap_without_changing_contract():
    parsed = ParsedInput(
        project_summary="FastAPI 모델 API",
        tech_stack=["FastAPI"],
        concerns=["배포 경험이 부족하다"],
        user_goal="안정적인 배포",
    )
    rule_gap = analyze_project_gap(parsed)
    reviewed = {
        **rule_gap.model_dump(),
        "main_gap": "운영 가능한 배포 구조 설계 역량 부족",
        "gap_categories": ["Infra", "MLOps", "DevOps"],
    }

    result = _review_gap_with_solar(parsed, rule_gap, FakeGapSolar(reviewed))

    assert isinstance(result, GapContext)
    assert result.main_gap == "운영 가능한 배포 구조 설계 역량 부족"
    assert set(result.model_dump()) == set(rule_gap.model_dump())


def test_gap_review_preserves_rule_result_when_solar_fails():
    parsed = ParsedInput(project_summary="추천 서비스", user_goal="멘토 추천")
    rule_gap = analyze_project_gap(parsed)

    result = _review_gap_with_solar(
        parsed, rule_gap, FakeGapSolar(error=OSError("temporary failure"))
    )

    assert result == rule_gap


def test_gap_review_rejects_categories_outside_existing_taxonomy():
    parsed = ParsedInput(
        project_summary="FastAPI 모델 API",
        concerns=["배포가 어렵다"],
        user_goal="안정적인 배포",
    )
    rule_gap = analyze_project_gap(parsed)
    invalid_review = {
        **rule_gap.model_dump(),
        "gap_categories": ["Invented Category"],
        "source_fields": ["not_a_parsed_field"],
    }

    result = _review_gap_with_solar(parsed, rule_gap, FakeGapSolar(invalid_review))

    assert result == rule_gap


def test_gap_review_prompt_and_output_preserve_specific_observability_need():
    parsed = ParsedInput(
        project_summary="백엔드 서비스의 인프라 역량을 높이고 싶다",
        tech_stack=["FastAPI"],
        concerns=["로그 관측 측면의 역량이 필요하다"],
        user_goal="로그를 기반으로 운영 문제를 빠르게 찾고 싶다",
    )
    rule_gap = analyze_project_gap(parsed)
    reviewed = {
        **rule_gap.model_dump(),
        "gap_categories": ["Infra", "MLOps", "DevOps"],
        "needed_mentor_expertise": [
            "로그 관측성 체계 설계",
            "로그·메트릭·트레이싱 기반 장애 분석",
        ],
        "query_hints": ["observability", "logging", "metrics", "tracing"],
    }
    solar = InspectingGapSolar(reviewed)

    result = _review_gap_with_solar(parsed, rule_gap, solar)

    assert result.gap_categories == ["Infra", "MLOps", "DevOps"]
    assert "로그 관측성 체계 설계" in result.needed_mentor_expertise
    assert "observability" in result.query_hints
    assert "specific professional need" in solar.system_prompt
    assert "로그 관측성 체계 설계" in solar.system_prompt

import unittest

from backend.app.nodes.input_parser import (
    parse_input,
    _check_sufficiency_rule_based,
    _merge_clarify_answer,
)

PARSED_INPUT_FIELDS = frozenset({
    "project_summary",
    "tech_stack",
    "current_stage",
    "concerns",
    "domain",
    "constraints",
    "user_goal",
})

SUFFICIENT_STATE = {
    "user_input": "Python과 FastAPI로 여행 일정 추천 API 서버를 개발 중인데, DB 설계 방법을 모르겠습니다.",
    "tech_stack": ["Python", "FastAPI"],
    "stage": "MVP 개발 중",
    "clarify_answer": None,
}


# ─────────────────────────────────────────────────────────────
# _check_sufficiency_rule_based 단위 테스트
# ─────────────────────────────────────────────────────────────

class TestCheckSufficiencyRuleBased(unittest.TestCase):
    def test_short_text_is_insufficient(self):
        ok, question, options = _check_sufficiency_rule_based("앱 만들어요", [])
        assert ok is False
        assert question
        assert len(options) > 0

    def test_no_tech_info_is_insufficient(self):
        ok, question, _ = _check_sufficiency_rule_based(
            "멘토링이 필요합니다. 현재 개발이 어렵고 막히는 부분이 많습니다.", []
        )
        assert ok is False
        assert question

    def test_no_concern_is_insufficient(self):
        ok, question, _ = _check_sufficiency_rule_based(
            "Python과 FastAPI로 여행 일정 추천 API 서버를 개발 중입니다.", []
        )
        assert ok is False
        assert question

    def test_sufficient_input_returns_true(self):
        ok, question, options = _check_sufficiency_rule_based(
            "Python과 FastAPI로 여행 일정 API를 만들고 있는데, DB 설계를 모르겠습니다.", []
        )
        assert ok is True
        assert question == ""
        assert options == []

    def test_tech_stack_param_substitutes_text_tech(self):
        """tech_stack 파라미터만 있어도 기술 정보 충분으로 판단한다."""
        ok, _, _ = _check_sufficiency_rule_based(
            "서비스를 만들고 있는데 배포 방법이 어렵습니다.", ["Python", "Django"]
        )
        assert ok is True


# ─────────────────────────────────────────────────────────────
# _merge_clarify_answer 단위 테스트
# ─────────────────────────────────────────────────────────────

class TestMergeClarifyAnswer(unittest.TestCase):
    def test_merged_contains_both_texts(self):
        merged = _merge_clarify_answer("원본 텍스트입니다.", "추가 설명입니다.")
        assert "원본 텍스트입니다." in merged
        assert "추가 설명입니다." in merged

    def test_merged_is_string(self):
        result = _merge_clarify_answer("A", "B")
        assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────
# parse_input 노드 통합 테스트
# ─────────────────────────────────────────────────────────────

class TestParseInput(unittest.TestCase):
    def test_sufficient_input_sets_is_sufficient_true(self):
        result = parse_input(SUFFICIENT_STATE)
        assert result["is_input_sufficient"] is True

    def test_sufficient_input_produces_parsed_input(self):
        result = parse_input(SUFFICIENT_STATE)
        assert result["parsed_input"]

    def test_insufficient_input_sets_is_sufficient_false(self):
        state = {**SUFFICIENT_STATE, "user_input": "앱 만들어요", "tech_stack": [], "clarify_answer": None}
        result = parse_input(state)
        assert result["is_input_sufficient"] is False

    def test_insufficient_input_sets_clarification_question(self):
        state = {**SUFFICIENT_STATE, "user_input": "앱 만들어요", "tech_stack": [], "clarify_answer": None}
        result = parse_input(state)
        assert result.get("clarification_question")

    def test_insufficient_input_parsed_input_is_empty(self):
        state = {**SUFFICIENT_STATE, "user_input": "앱 만들어요", "tech_stack": [], "clarify_answer": None}
        result = parse_input(state)
        assert result["parsed_input"] == {}

    def test_parsed_input_has_exact_schema_fields(self):
        result = parse_input(SUFFICIENT_STATE)
        assert set(result["parsed_input"].keys()) == PARSED_INPUT_FIELDS

    def test_tech_stack_is_reflected_in_parsed_input(self):
        state = {**SUFFICIENT_STATE, "tech_stack": ["React", "Node.js"]}
        result = parse_input(state)
        assert "React" in result["parsed_input"]["tech_stack"]

    def test_stage_is_reflected_in_parsed_input(self):
        result = parse_input(SUFFICIENT_STATE)
        assert result["parsed_input"]["current_stage"] == "MVP 개발 중"

    def test_stage_defaults_to_undecided_when_empty(self):
        state = {**SUFFICIENT_STATE, "stage": ""}
        result = parse_input(state)
        assert result["parsed_input"]["current_stage"] == "미정"

    def test_clarify_answer_skips_sufficiency_check(self):
        """clarify_answer가 있으면 원본 입력이 짧아도 parsed_input을 생성한다."""
        state = {
            "user_input": "앱 만들어요",
            "tech_stack": [],
            "stage": "",
            "clarify_answer": "Django로 쇼핑몰을 만들고 있는데 배포 방법을 모릅니다.",
        }
        result = parse_input(state)
        assert result["is_input_sufficient"] is True
        assert result["parsed_input"]

    def test_clarify_answer_merged_into_user_input(self):
        state = {
            "user_input": "원본 텍스트",
            "tech_stack": [],
            "stage": "",
            "clarify_answer": "추가 설명입니다",
        }
        result = parse_input(state)
        assert "추가 설명입니다" in result["user_input"]

    def test_clarify_answer_no_extra_question_generated(self):
        state = {
            "user_input": "앱 만들어요",
            "tech_stack": [],
            "stage": "",
            "clarify_answer": "Django로 쇼핑몰을 만들고 있는데 배포가 어렵습니다.",
        }
        result = parse_input(state)
        assert result.get("clarification_question") == ""


if __name__ == "__main__":
    unittest.main()

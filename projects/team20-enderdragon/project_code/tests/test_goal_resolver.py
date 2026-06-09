"""resolve_goal 노드 테스트.

LLM 분류 자체는 비결정적이라, LLM을 가짜로 교체해 노드가 구조화 출력을
상태 키로 올바르게 옮기는지와, 결정론 부분(추천 목표 블록·제안 목표의 제작 분석 연동)을
검증한다.
"""
from app.agents import goal_resolver
from app.agents.material_checker import check_materials
from app.prompts.templates import format_goal_block
from app.schemas import GoalResolution


class _FakeStructuredLLM:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class _FakeLLM:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema):
        return _FakeStructuredLLM(self._result)


def _patch_llm(monkeypatch, result):
    monkeypatch.setattr(goal_resolver, "get_llm", lambda **_: _FakeLLM(result))


def test_명시적_목표는_그대로_분류하고_제안하지_않는다(monkeypatch):
    _patch_llm(monkeypatch, GoalResolution(
        goal_class="craft", goal_text="철 곡괭이 만들기", proposed=False))
    out = goal_resolver.resolve_goal({"query": "철 곡괭이 만들래"})
    assert out == {"goal_class": "craft", "resolved_goal": "철 곡괭이 만들기", "goal_proposed": False}


def test_막연한_질문이면_목표를_제안한다(monkeypatch):
    _patch_llm(monkeypatch, GoalResolution(
        goal_class="craft", goal_text="돌 곡괭이 만들기", proposed=True))
    out = goal_resolver.resolve_goal({
        "query": "이제 뭐하지?",
        "inventory": [{"item": "minecraft:cobblestone", "count": 5}],
        "inventory_connected": True,
    })
    assert out["goal_class"] == "craft"
    assert out["resolved_goal"] == "돌 곡괭이 만들기"
    assert out["goal_proposed"] is True


def test_LLM_실패하면_빈_업데이트(monkeypatch):
    class _Boom:
        def with_structured_output(self, _schema):
            raise RuntimeError("LLM down")
    monkeypatch.setattr(goal_resolver, "get_llm", lambda **_: _Boom())
    assert goal_resolver.resolve_goal({"query": "이제 뭐하지?"}) == {}


def test_추천_목표_블록은_제안일_때만_나온다():
    assert format_goal_block("돌 곡괭이 만들기", True).startswith("[추천 목표]")
    assert "돌 곡괭이 만들기" in format_goal_block("돌 곡괭이 만들기", True)
    # 사용자가 직접 밝힌 목표(proposed=False)나 빈 목표면 블록 없음
    assert format_goal_block("철 곡괭이 만들기", False) == ""
    assert format_goal_block("", True) == ""


def test_제안된_제작목표도_부족자원을_계산한다():
    # query엔 제작 대상이 없지만, resolve_goal이 제안한 목표 문장에서 찾아 분석한다.
    out = check_materials({
        "query": "이제 뭐하지?",
        "resolved_goal": "철 곡괭이 만들기",
        "inventory": [],
    })
    assert out["goal_key"] == "minecraft:iron_pickaxe"
    assert any(g["item"] == "minecraft:raw_iron" for g in out["material_plan"]["gather"])

"""check_materials 노드·목표 해석기 테스트.

질문에서 제작 목표를 집어내고, plan_materials 결과가 프롬프트 블록으로 반영되는지 검증한다.
"""
from app.knowledge.goal_resolver import resolve_craft_target
from app.agents.material_checker import check_materials
from app.prompts.templates import format_material_plan_block


def test_제작_목표를_item_id로_해석한다():
    assert resolve_craft_target("철 곡괭이 만들고 싶어") == "minecraft:iron_pickaxe"
    assert resolve_craft_target("화로 어떻게 만들어?") == "minecraft:furnace"


def test_가장_먼저_언급된_목표를_택한다():
    # "철 곡괭이 만들려면 돌 곡괭이가…" → 목표는 먼저 나온 철 곡괭이
    assert resolve_craft_target("철 곡괭이 만들려면 돌 곡괭이가 필요해?") == "minecraft:iron_pickaxe"


def test_제작_대상이_아니면_None():
    assert resolve_craft_target("철광석 어디서 캐?") is None  # 철광석은 제작 대상 아님
    assert resolve_craft_target("안녕") is None


def test_check_materials_노드가_부족자원을_싣는다():
    out = check_materials({"query": "철 곡괭이 만들고 싶어", "inventory": []})
    assert out["goal_key"] == "minecraft:iron_pickaxe"
    gap = out["material_plan"]
    assert gap["ready"] is False
    assert any(g["item"] == "minecraft:raw_iron" for g in gap["gather"])


def test_제작_목표_없으면_빈_업데이트():
    assert check_materials({"query": "안녕!", "inventory": []}) == {}


def test_부족자원_블록은_차단_재료를_표시한다():
    gap = check_materials({"query": "철 곡괭이 만들고 싶어", "inventory": []})["material_plan"]
    block = format_material_plan_block("minecraft:iron_pickaxe", gap)
    assert "철 곡괭이" in block
    assert "철 원석" in block
    assert "곡괭이 이상이 있어야" in block  # raw_iron 채굴 차단(곡괭이 없음)


def test_재료_충분하면_바로_제작_안내():
    inv = [{"item": "minecraft:iron_ingot", "count": 3}, {"item": "minecraft:stick", "count": 2}]
    gap = check_materials({"query": "철 곡괭이 만들래", "inventory": inv})["material_plan"]
    block = format_material_plan_block("minecraft:iron_pickaxe", gap)
    assert "바로 제작" in block


def test_제작_목표면_3x3_격자를_싣는다():
    out = check_materials({"query": "철 곡괭이 만들고 싶어", "inventory": []})
    recipe = out["recipe"]
    assert recipe["output"] == "minecraft:iron_pickaxe"
    assert len(recipe["grid"]) == 9
    # 철 곡괭이: 윗줄 철 주괴 3, 가운데/아랫줄 가운데 막대기
    assert recipe["grid"][:3] == ["minecraft:iron_ingot"] * 3
    assert recipe["grid"][4] == "minecraft:stick"
    assert recipe["grid"][7] == "minecraft:stick"

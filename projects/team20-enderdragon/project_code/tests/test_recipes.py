"""app.knowledge.recipes 로더 회귀 테스트.

게임 jar에서 추출한 recipes.json이 올바르게 로드되고, 대표 레시피·3x3 배치·
태그 해석·가열 레시피가 기대대로 들어있는지 검증한다.
"""
from app.knowledge import recipes


def test_철_곡괭이_3x3_배치와_재료가_정확하다():
    variants = recipes.craft_recipes("minecraft:iron_pickaxe")
    assert variants, "철 곡괭이 레시피가 있어야 한다"
    r = variants[0]
    assert r["pattern"] == ["XXX", " # ", " # "]
    assert r["reqs"] == {"minecraft:iron_ingot": 3, "minecraft:stick": 2}
    assert r["key"]["X"]["item"] == "minecraft:iron_ingot"
    assert r["key"]["#"]["item"] == "minecraft:stick"


def test_막대기_대표_레시피는_판자다():
    # 막대기는 판자·대나무 두 레시피가 있는데, 대표(파일명=결과물명)가 앞에 와야 한다.
    variants = recipes.craft_recipes("minecraft:stick")
    assert len(variants) >= 2
    assert variants[0]["recipe_id"] == "stick"
    assert "minecraft:planks" in variants[0]["reqs"]


def test_화로_레시피는_돌재료_태그를_쓰고_대표는_조약돌이다():
    r = recipes.craft_recipes("minecraft:furnace")[0]
    slot = r["key"]["#"]
    assert slot["tag"] == "minecraft:stone_crafting_materials"
    assert slot["item"] == "minecraft:cobblestone"  # 렌더·대체용 대표
    assert recipes.tag_members("minecraft:stone_crafting_materials")


def test_철_주괴는_가열_레시피로_얻는다():
    cooking = recipes.cooking_recipes("minecraft:iron_ingot")
    ingredients = {v["ingredient"]["item"] for v in cooking}
    assert "minecraft:raw_iron" in ingredients
    assert {v["method"] for v in cooking} <= {"smelting", "blasting"}


def test_없는_아이템은_빈_목록이다():
    assert recipes.craft_recipes("minecraft:not_a_real_item") == []
    assert recipes.is_craftable("minecraft:iron_pickaxe")
    assert not recipes.is_craftable("minecraft:not_a_real_item")


def test_격자는_pattern을_좌상단_정렬로_9칸에_배치한다():
    grid = recipes.recipe_grid("minecraft:iron_pickaxe")
    assert grid["output"] == "minecraft:iron_pickaxe"
    assert grid["count"] == 1
    assert grid["grid"] == [
        "minecraft:iron_ingot", "minecraft:iron_ingot", "minecraft:iron_ingot",
        None, "minecraft:stick", None,
        None, "minecraft:stick", None,
    ]


def test_격자의_태그칸은_대표_아이템으로_채운다():
    # 화로: 8칸 stone_crafting_materials 태그 → 대표 조약돌, 가운데만 빈 칸
    grid = recipes.recipe_grid("minecraft:furnace")["grid"]
    assert grid[4] is None
    assert all(c == "minecraft:cobblestone" for i, c in enumerate(grid) if i != 4)


def test_shaped가_아니면_격자는_None():
    assert recipes.recipe_grid("minecraft:raw_iron") is None         # 채굴로만 얻음(제작 불가)
    assert recipes.recipe_grid("minecraft:not_a_real_item") is None

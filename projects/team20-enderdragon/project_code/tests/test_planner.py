"""app.knowledge.planner.plan_materials 결정론 엔진 테스트.

목표 아이템 + 인벤토리로 부족 자원·획득 경로·채굴 티어 차단을 정확히 계산하는지
검증한다(대표 시나리오 '철 곡괭이'·'첫 도구' 중심).
"""
from app.knowledge import planner


def gather_by_item(result: dict) -> dict[str, dict]:
    return {g["item"]: g for g in result["gather"]}


def test_빈손이면_철곡괭이는_원석과_나무를_채굴해야_한다():
    r = planner.plan_materials("minecraft:iron_pickaxe", [])
    assert not r["ready"]
    g = gather_by_item(r)
    assert g["minecraft:raw_iron"]["qty"] == 3
    assert g["minecraft:oak_log"]["qty"] == 1


def test_곡괭이가_없으면_철원석_채굴이_차단된다():
    r = planner.plan_materials("minecraft:iron_pickaxe", [])
    raw_iron = gather_by_item(r)["minecraft:raw_iron"]
    assert raw_iron["mining_tier"] == 1
    assert raw_iron["blocked"] is True
    assert any(b["item"] == "minecraft:raw_iron" for b in r["blocked"])


def test_돌곡괭이가_있으면_철원석_채굴이_가능하다():
    r = planner.plan_materials("minecraft:iron_pickaxe", [{"item": "minecraft:stone_pickaxe", "count": 1}])
    raw_iron = gather_by_item(r)["minecraft:raw_iron"]
    assert raw_iron["blocked"] is False
    assert r["blocked"] == []


def test_재료가_충분하면_바로_제작_가능하다():
    inv = [{"item": "minecraft:iron_ingot", "count": 3}, {"item": "minecraft:stick", "count": 2}]
    r = planner.plan_materials("minecraft:iron_pickaxe", inv)
    assert r["ready"] is True
    assert r["gather"] == []


def test_원석을_보유하면_제련만으로_충당된다():
    # 곡괭이가 없어도 이미 raw_iron을 들고 있으면 채굴이 필요 없다(제련만 하면 됨).
    inv = [{"item": "minecraft:raw_iron", "count": 3}, {"item": "minecraft:stick", "count": 2}]
    r = planner.plan_materials("minecraft:iron_pickaxe", inv)
    assert r["ready"] is True


def test_철주괴는_저장블록이_아니라_제련으로_분해된다():
    # iron_ingot의 제작 레시피는 iron_block 압축 해제뿐 → 가열(제련) 경로를 택해야 한다.
    tree = planner.plan_materials("minecraft:iron_ingot", [])["tree"]
    assert tree["status"] == "cook"
    assert tree["method"] == "smelting"
    assert tree["children"][0]["item"] == "minecraft:raw_iron"


def test_화로는_조약돌_8개가_필요하고_곡괭이없이는_막힌다():
    r = planner.plan_materials("minecraft:furnace", [])
    cobble = gather_by_item(r)["minecraft:cobblestone"]
    assert cobble["qty"] == 8
    assert cobble["mining_tier"] == 0
    assert cobble["blocked"] is True  # 돌 계열은 최소한 나무 곡괭이가 있어야 캘 수 있다


def test_다이아는_철곡괭이가_있어야_캘_수_있다():
    # 돌 곡괭이(레벨1)로는 다이아몬드(티어2)를 캘 수 없다.
    r = planner.plan_materials("minecraft:diamond_pickaxe", [{"item": "minecraft:stone_pickaxe", "count": 1}])
    diamond = gather_by_item(r)["minecraft:diamond"]
    assert diamond["mining_tier"] == 2
    assert diamond["blocked"] is True


def test_침대는_양털을_수집하지_실로_제작하지_않는다():
    # 양털은 실 4개로 제작 가능하지만, 초보의 자연스러운 획득은 양 깎기다.
    r = planner.plan_materials("minecraft:white_bed", [])
    g = gather_by_item(r)
    assert g["minecraft:white_wool"]["qty"] == 3
    assert "minecraft:string" not in g  # 실로 분해하면 안 됨


def test_빵은_밀을_수집하지_건초더미로_분해하지_않는다():
    # 밀↔건초더미는 저장블록 압축 해제 관계 → 밀을 직접 수집해야 한다.
    r = planner.plan_materials("minecraft:bread", [])
    g = gather_by_item(r)
    assert g["minecraft:wheat"]["qty"] == 3
    assert "minecraft:hay_block" not in g


def test_곡괭이_레벨과_채굴티어_헬퍼():
    assert planner.best_pickaxe_level({"minecraft:stone_pickaxe": 1}) == 1
    assert planner.best_pickaxe_level({"minecraft:golden_pickaxe": 1}) == 0  # 금=나무 동급
    assert planner.best_pickaxe_level({}) == -1
    assert planner.mining_tier("minecraft:raw_iron") == 1
    assert planner.mining_tier("minecraft:diamond") == 2
    assert planner.mining_tier("minecraft:oak_log") is None  # 손으로 캐는 건 채굴 아님


def test_next_action_재료_충분하면_제작():
    assert planner.next_action({"ready": True, "gather": []}) == {"kind": "craft"}


def test_next_action_막히지_않은_낮은_티어부터():
    # 막대기(채굴 아님, tier None=0)와 막힌 철 원석 → 막대기를 먼저.
    plan = {"ready": False, "gather": [
        {"item": "minecraft:raw_iron", "qty": 3, "mining_tier": 1, "blocked": True},
        {"item": "minecraft:stick", "qty": 2, "blocked": False},
    ]}
    nxt = planner.next_action(plan)
    assert nxt["kind"] == "gather" and nxt["item"] == "minecraft:stick"


def test_next_action_전부_막히면_가장_낮은_티어_선행():
    plan = {"ready": False, "gather": [
        {"item": "minecraft:diamond", "qty": 1, "mining_tier": 2, "blocked": True},
        {"item": "minecraft:raw_iron", "qty": 3, "mining_tier": 1, "blocked": True},
    ]}
    nxt = planner.next_action(plan)
    assert nxt["item"] == "minecraft:raw_iron"  # 티어 1 < 2


def test_next_action_빈_플랜은_None():
    assert planner.next_action({"ready": False, "gather": []}) is None

"""결정론 제작 플래너 — 목표 아이템과 인벤토리로 '부족 자원·획득 경로'를 계산한다.

LLM 산수를 믿지 않고, [recipes](recipes.py)의 게임 추출 데이터로 직접 계산한다:
목표를 제작(craft)·제련(cook)·채굴/수집(gather)으로 재귀 분해하고, 채굴 티어가
현재 곡괭이로 부족하면 차단(blocked)으로 표시한다. plan_verifier·resource_gap_analyzer가 사용.

반환 트리(노드)의 status:
  - have   : 인벤토리로 충당됨
  - craft  : 작업대 제작 (recipe·children)
  - cook   : 화로/용광로 제련 (method·children)
  - gather : 더 분해할 수 없는 기초 재료 — 직접 캐거나 모아야 함 (mining_tier·blocked)
"""
from math import ceil

from app.knowledge import recipes

MAX_DEPTH = 8  # 제작 트리 재귀 한계(순환·과도 분해 방지)

# 곡괭이 종류 → 채굴 레벨 (금 곡괭이는 나무와 동급인 0)
PICKAXE_LEVELS = {"wooden": 0, "golden": 0, "stone": 1, "iron": 2, "diamond": 3, "netherite": 4}

# 채굴로 얻는 기초 재료 → 캐야 하는 원본 블록 (아이템ID와 블록ID가 다른 경우의 다리).
# 채굴 티어는 recipes.MINING(블록 기준)에서 가져온다.
RAW_SOURCES = {
    "minecraft:coal": "minecraft:coal_ore",
    "minecraft:raw_iron": "minecraft:iron_ore",
    "minecraft:raw_gold": "minecraft:gold_ore",
    "minecraft:raw_copper": "minecraft:copper_ore",
    "minecraft:diamond": "minecraft:diamond_ore",
    "minecraft:emerald": "minecraft:emerald_ore",
    "minecraft:redstone": "minecraft:redstone_ore",
    "minecraft:lapis_lazuli": "minecraft:lapis_ore",
    "minecraft:quartz": "minecraft:nether_quartz_ore",
    "minecraft:cobblestone": "minecraft:stone",
}

# 몹/농사 등에서 얻는 기초 재료. 제작 레시피가 있어도(예: 양털←실 4) 초보의 자연스러운
# 획득은 양 깎기·소 잡기다. 분해하지 않고 수집으로 멈춰, '어떻게 얻는지'는 코칭(LLM+RAG)에 맡긴다.
GATHERED_BASE = {"minecraft:leather"}


def _is_base_gathered(item_id: str) -> bool:
    return item_id in GATHERED_BASE or item_id.endswith("_wool")


def best_pickaxe_level(inventory: dict[str, int]) -> int:
    """인벤토리에서 가장 좋은 곡괭이의 채굴 레벨. 곡괭이가 없으면 -1."""
    level = -1
    for item_id, count in inventory.items():
        if count > 0 and item_id.endswith("_pickaxe"):
            kind = item_id.removeprefix("minecraft:").removesuffix("_pickaxe")
            level = max(level, PICKAXE_LEVELS.get(kind, 0))
    return level


def mining_tier(item_id: str) -> int | None:
    """채굴로 얻는 기초 재료면 필요한 곡괭이 레벨, 자유 수집(나무·작물 등)이면 None."""
    block = item_id if item_id in recipes.MINING else RAW_SOURCES.get(item_id)
    if block is None:
        return None
    return recipes.block_mining_level(block)


def _ingredient_token(ing: dict | None) -> str | None:
    return None if ing is None else (ing.get("tag") or ing.get("item"))


def _pick_craft(item_id: str, path: list[str]) -> dict | None:
    """순환·압축 해제를 배제한 첫 제작 레시피(대표 우선). 없으면 None."""
    for variant in recipes.craft_recipes(item_id):
        if any(token in path for token in variant["reqs"]):
            continue  # 순환 (조상 재료 재등장)
        if _is_unpacking(variant):
            continue  # 저장블록 압축 해제 (예: 건초더미 1→밀 9, 철블록 1→주괴 9)
        return variant
    return None


def _is_unpacking(variant: dict) -> bool:
    """저장 블록을 푸는 레시피인지: 단일 재료 1개로 9개 이상을 만든다(밀·주괴 등).

    이런 레시피로 기초 재료를 '제작'한다고 안내하면 비현실적이라 배제한다.
    (반대로 블록을 '만드는' 9개→1개 레시피는 result_count가 작아 걸리지 않는다.)
    """
    reqs = variant["reqs"]
    return len(reqs) == 1 and next(iter(reqs.values())) == 1 and variant["result_count"] >= 9


def _is_raw_ingredient(token: str | None) -> bool:
    return bool(token) and (token in RAW_SOURCES or "raw_" in token)


def _pick_cook(item_id: str) -> dict | None:
    """가열 레시피 중 가장 자연스러운 것: 제련(smelting) 우선, 원석/raw 재료 우선."""
    candidates = recipes.cooking_recipes(item_id)
    if not candidates:
        return None
    return min(candidates, key=lambda r: (
        r.get("method") != "smelting",
        not _is_raw_ingredient(_ingredient_token(r.get("ingredient"))),
    ))


def plan_materials(target_id: str, inventory: dict[str, int] | list[dict], qty: int = 1) -> dict:
    """목표 아이템 qty개를 만들기 위한 부족 자원·획득 경로 트리를 계산한다.

    inventory는 {item_id: count} 또는 모드가 보내는 [{"item","count"}] 둘 다 받는다.
    """
    have = _normalize_inventory(inventory)
    pickaxe = best_pickaxe_level(have)
    tree = _resolve(target_id, qty, have, pickaxe, path=[], depth=0)
    gather = _flatten_gather(tree)
    return {
        "tree": tree,
        "gather": gather,  # [{item, qty, mining_tier, blocked}] — 직접 캐거나 모을 기초 재료
        "blocked": [g for g in gather if g["blocked"]],
        "ready": not gather,  # 더 캘 것 없이 인벤토리만으로 제작 가능
    }


def next_action(plan: dict) -> dict | None:
    """플랜에서 지금 할 '다음 한 단계'를 결정론적으로 고른다(없으면 None).

    - 재료가 다 갖춰졌으면(ready) 제작 단계.
    - 아니면 아직 모을 재료 중 '지금 캘 수 있는'(막히지 않은) 것을 우선, 그 안에서 채굴
      티어가 낮은(맨손에 가까운) 기초 재료부터.
    - 전부 막혀 있으면 막힌 재료 중 티어가 가장 낮은 것(먼저 곡괭이를 마련해야 하는 선행 단계).
    """
    if plan.get("ready"):
        return {"kind": "craft"}
    gather = plan.get("gather", [])
    if not gather:
        return None
    actionable = [g for g in gather if not g.get("blocked")]
    pool = actionable or gather
    nxt = min(pool, key=lambda g: (g.get("mining_tier") or 0))
    return {"kind": "gather", **nxt}


def _normalize_inventory(inventory: dict[str, int] | list[dict]) -> dict[str, int]:
    if isinstance(inventory, dict):
        return dict(inventory)
    counts: dict[str, int] = {}
    for entry in inventory:
        counts[entry["item"]] = counts.get(entry["item"], 0) + entry["count"]
    return counts


def _resolve(token: str, qty: int, have: dict[str, int], pickaxe: int, path: list[str], depth: int) -> dict:
    is_tag = recipes.is_tag(token)
    candidates = recipes.tag_members(token) if is_tag else [token]

    taken = _consume(have, candidates, qty)
    node: dict = {"item": token, "qty": qty, "have": taken}
    if is_tag:
        node["is_tag"] = True
        node["members"] = candidates[:6]
    remaining = qty - taken
    if remaining <= 0:
        node["status"] = "have"
        return node

    node["need"] = remaining
    target = token if not is_tag else (candidates[0] if candidates else None)
    if is_tag and target is not None:
        node["item"] = target            # 태그 → 대표 구체 아이템으로 표시(렌더·번역 가능)
        node["any_of"] = candidates[:6]

    # 더 분해 불가(미지의 재료·깊이 초과·순환) → 수집으로 종료
    if target is None or depth >= MAX_DEPTH or target in path:
        return _as_gather(node, target, pickaxe)

    # 기초 재료는 분해하지 않고 바로 수집한다.
    #  - 채굴(원석·다이아·조약돌): 원석↔저장블록 압축 해제로 엉뚱하게 분해되는 것을 막는다.
    #  - 몹/농사(양털·가죽): 제작 레시피가 있어도 자연스러운 획득은 수집이다.
    if mining_tier(target) is not None or _is_base_gathered(target):
        return _as_gather(node, target, pickaxe)

    # 제련 결과물(주괴·유리·돌 등)은 제작보다 가열이 자연스러운 경로다.
    # (금속 주괴의 제작 레시피는 블록/조각 압축 해제뿐이라 가열을 먼저 시도한다.)
    cook = _pick_cook(target)
    if cook and _ingredient_token(cook["ingredient"]):
        node["status"] = "cook"
        node["method"] = cook["method"]
        node["children"] = [
            _resolve(_ingredient_token(cook["ingredient"]), remaining, have, pickaxe, path + [target], depth + 1)
        ]
        return node

    variant = _pick_craft(target, path)
    if variant:
        node["status"] = "craft"
        node["recipe"] = variant
        batches = ceil(remaining / variant["result_count"])
        node["children"] = [
            _resolve(req, count * batches, have, pickaxe, path + [target], depth + 1)
            for req, count in variant["reqs"].items()
        ]
        return node

    return _as_gather(node, target, pickaxe)


def _consume(have: dict[str, int], candidates: list[str], qty: int) -> int:
    """인벤토리에서 candidates(태그면 여러 멤버)를 합쳐 최대 qty개까지 소비하고, 소비량 반환."""
    taken = 0
    for item_id in candidates:
        if taken >= qty:
            break
        use = min(have.get(item_id, 0), qty - taken)
        if use:
            have[item_id] -= use
            taken += use
    return taken


def _as_gather(node: dict, item_id: str | None, pickaxe: int) -> dict:
    node["status"] = "gather"
    tier = mining_tier(item_id) if item_id else None
    if tier is not None:
        node["mining_tier"] = tier
        if pickaxe < tier:
            node["blocked"] = True
            node["blocked_reason"] = f"곡괭이 레벨 {tier} 이상 필요 (현재 {max(pickaxe, 0)})"
    return node


def _flatten_gather(tree: dict) -> list[dict]:
    """트리에서 gather 노드를 모아 아이템별 합계로 집계한다."""
    totals: dict[str, dict] = {}

    def walk(node: dict) -> None:
        if node.get("status") == "gather":
            item = node["item"]
            agg = totals.setdefault(item, {
                "item": item, "qty": 0,
                "mining_tier": node.get("mining_tier"),
                "blocked": bool(node.get("blocked")),
            })
            agg["qty"] += node.get("need", node["qty"])
        for child in node.get("children", []):
            walk(child)

    walk(tree)
    return list(totals.values())

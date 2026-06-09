"""마인크래프트 게임 jar에서 제작 레시피를 추출해 app/knowledge/recipes.json으로 굽는다.

위키 텍스트(RAG)나 LLM 추측이 아니라 **게임의 공식 레시피 데이터**가 정답이므로,
MC 1.21.1 jar의 data/minecraft/recipe/*.json을 그대로 파싱한다. 한 번 굽고 나면
런타임은 jar 없이 recipes.json만 읽으면 된다(읽기전용·고정 데이터).

사용 예:
  uv run python scripts/extract_recipes.py
  uv run python scripts/extract_recipes.py --jar ~/.gradle/caches/fabric-loom/1.21.1/minecraft-merged.jar

추출 대상 타입:
  - crafting_shaped     : 3x3 배치(pattern+key) → 격자 렌더용
  - crafting_shapeless  : 재료 목록
  - smelting/blasting/smoking/campfire_cooking : 가열(화로/용광로/훈연/모닥불)
  - stonecutting        : 석재 절단기

태그 재료(예: "minecraft:planks")는 태그 JSON으로 해석해 대표 아이템을 함께 담는다.
"""
import argparse
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

DEFAULT_JAR = Path.home() / ".gradle/caches/fabric-loom/1.21.1/minecraft-merged.jar"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "app/knowledge/recipes.json"

RECIPE_DIR = "data/minecraft/recipe/"
ITEM_TAG_DIR = "data/minecraft/tags/item/"
BLOCK_TAG_DIR = "data/minecraft/tags/block/"

# 블록 채굴 티어: 해당 태그에 속한 블록은 그 레벨 이상의 곡괭이로만 캘 수 있다.
# (곡괭이 레벨: 나무·금=0, 돌=1, 철=2, 다이아=3, 네더라이트=4)
MINING_TIER_TAGS = {
    "minecraft:needs_stone_tool": 1,
    "minecraft:needs_iron_tool": 2,
    "minecraft:needs_diamond_tool": 3,
}

# 굽는 타입. crafting_special_*(프로그램 생성)·smithing_trim(장식)은 데이터가 없어 제외.
CRAFTING_TYPES = {"minecraft:crafting_shaped", "minecraft:crafting_shapeless"}
COOKING_TYPES = {
    "minecraft:smelting",
    "minecraft:blasting",
    "minecraft:smoking",
    "minecraft:campfire_cooking",
}


def load_tags(jar: zipfile.ZipFile, tag_dir: str) -> dict[str, list[str]]:
    """태그 디렉토리를 {태그ID: [ID...]}로 로드한다(중첩 태그 재귀 해석, 순서 보존)."""
    raw: dict[str, list[str]] = {}
    for name in jar.namelist():
        if name.startswith(tag_dir) and name.endswith(".json"):
            tag_id = "minecraft:" + name[len(tag_dir):-len(".json")]
            values = json.loads(jar.read(name)).get("values", [])
            raw[tag_id] = [v["id"] if isinstance(v, dict) else v for v in values]

    resolved: dict[str, list[str]] = {}

    def resolve(tag_id: str, seen: set[str]) -> list[str]:
        if tag_id in resolved:
            return resolved[tag_id]
        if tag_id in seen:  # 순환 방지
            return []
        seen.add(tag_id)
        items: list[str] = []
        for entry in raw.get(tag_id, []):
            if entry.startswith("#"):  # 다른 태그 참조
                items.extend(resolve(entry[1:], seen))
            else:
                items.append(entry)
        deduped = list(dict.fromkeys(items))  # 순서 보존 중복 제거
        resolved[tag_id] = deduped
        return deduped

    for tag_id in raw:
        resolve(tag_id, set())
    return resolved


def resolve_ingredient(entry, tags: dict[str, list[str]]) -> dict | None:
    """레시피 재료 한 칸을 {item, tag?}로 정규화한다.

    - 구체 아이템: {"item": "minecraft:iron_ingot"}
    - 태그: {"tag": "minecraft:planks", "item": <대표 아이템>}  (item은 렌더/대체용 대표)
    - 옵션 목록([...])이면 첫 항목 사용. 빈 칸은 None.
    """
    if entry is None:
        return None
    if isinstance(entry, list):
        return resolve_ingredient(entry[0], tags) if entry else None
    if isinstance(entry, str):  # "#태그" 또는 아이템ID 문자열
        return resolve_ingredient({"tag": entry[1:]} if entry.startswith("#") else {"item": entry}, tags)
    if "item" in entry:
        return {"item": entry["item"]}
    if "tag" in entry:
        tag_id = entry["tag"] if ":" in entry["tag"] else "minecraft:" + entry["tag"]
        members = tags.get(tag_id, [])
        result = {"tag": tag_id}
        if members:
            result["item"] = members[0]  # 대표 아이템(렌더·대체용)
        return result
    return None


def ingredient_token(ing: dict | None) -> str | None:
    """부족 자원 계산용 단일 토큰(태그 우선, 없으면 아이템ID). 빈 칸은 None."""
    if ing is None:
        return None
    return ing.get("tag") or ing.get("item")


def parse_shaped(recipe: dict, tags: dict[str, list[str]]) -> dict:
    """crafting_shaped → {pattern, key, result_count, reqs}."""
    key = {char: resolve_ingredient(ing, tags) for char, ing in recipe.get("key", {}).items()}
    pattern = recipe["pattern"]
    counts: Counter[str] = Counter()
    for row in pattern:
        for char in row:
            if char != " " and key.get(char):
                token = ingredient_token(key[char])
                if token:
                    counts[token] += 1
    return {
        "pattern": pattern,
        "key": key,
        "result_count": recipe["result"].get("count", 1),
        "reqs": dict(counts),
    }


def parse_shapeless(recipe: dict, tags: dict[str, list[str]]) -> dict:
    """crafting_shapeless → {ingredients, result_count, reqs}."""
    ingredients = [resolve_ingredient(ing, tags) for ing in recipe.get("ingredients", [])]
    counts: Counter[str] = Counter()
    for ing in ingredients:
        token = ingredient_token(ing)
        if token:
            counts[token] += 1
    return {
        "ingredients": ingredients,
        "result_count": recipe["result"].get("count", 1),
        "reqs": dict(counts),
    }


def parse_cooking(recipe: dict, tags: dict[str, list[str]]) -> dict:
    """smelting/blasting/smoking/campfire_cooking → {ingredient, method}."""
    method = recipe["type"].split(":")[1]
    return {"ingredient": resolve_ingredient(recipe.get("ingredient"), tags), "method": method}


def parse_stonecutting(recipe: dict, tags: dict[str, list[str]]) -> dict:
    """stonecutting → {ingredient, result_count}."""
    return {
        "ingredient": resolve_ingredient(recipe.get("ingredient"), tags),
        "result_count": recipe["result"].get("count", 1),
    }


def extract(jar_path: Path) -> dict:
    # 한 결과물에 레시피가 여럿일 수 있어(예: 막대기=판자/대나무) 모두 리스트로 보존한다.
    # 그래야 "보유 재료로 만들 수 있는 레시피"를 골라줄 수 있다.
    shaped: dict[str, list[dict]] = {}
    shapeless: dict[str, list[dict]] = {}
    cooking: dict[str, list[dict]] = {}
    stonecutting: dict[str, list[dict]] = {}

    with zipfile.ZipFile(jar_path) as jar:
        tags = load_tags(jar, ITEM_TAG_DIR)
        mining = build_mining_tiers(load_tags(jar, BLOCK_TAG_DIR))
        for name in jar.namelist():
            if not (name.startswith(RECIPE_DIR) and name.endswith(".json")):
                continue
            recipe = json.loads(jar.read(name))
            rtype = recipe.get("type")
            result_id = recipe.get("result", {}).get("id")
            if not result_id:
                continue
            recipe_id = name[len(RECIPE_DIR):-len(".json")]
            if rtype == "minecraft:crafting_shaped":
                _append(shaped, result_id, parse_shaped(recipe, tags), recipe_id)
            elif rtype == "minecraft:crafting_shapeless":
                _append(shapeless, result_id, parse_shapeless(recipe, tags), recipe_id)
            elif rtype in COOKING_TYPES:
                _append(cooking, result_id, parse_cooking(recipe, tags), recipe_id)
            elif rtype == "minecraft:stonecutting":
                _append(stonecutting, result_id, parse_stonecutting(recipe, tags), recipe_id)
            # smithing_trim·crafting_special 등 나머지 타입은 건너뜀

    for recipes in (shaped, shapeless, cooking, stonecutting):
        _sort_canonical_first(recipes)

    used_tags = _collect_used_tags(shaped, shapeless, cooking, stonecutting)
    return {
        "_meta": {"source": jar_path.name, "type_counts": {
            "shaped": len(shaped), "shapeless": len(shapeless),
            "cooking": len(cooking), "stonecutting": len(stonecutting),
            "mining": len(mining),
        }},
        "shaped": shaped,
        "shapeless": shapeless,
        "cooking": cooking,
        "stonecutting": stonecutting,
        "mining": mining,
        "tags": {t: tags[t] for t in sorted(used_tags) if t in tags},
    }


def build_mining_tiers(block_tags: dict[str, list[str]]) -> dict[str, int]:
    """블록 채굴 티어 {블록ID: 최소 곡괭이 레벨}. 태그 없는 블록(레벨 0)은 담지 않는다."""
    mining: dict[str, int] = {}
    for tag_id, tier in MINING_TIER_TAGS.items():
        for block_id in block_tags.get(tag_id, []):
            mining[block_id] = max(mining.get(block_id, 0), tier)  # 겹치면 높은 티어
    return mining


def _append(recipes: dict[str, list[dict]], result_id: str, parsed: dict, recipe_id: str) -> None:
    parsed["recipe_id"] = recipe_id
    recipes.setdefault(result_id, []).append(parsed)


def _sort_canonical_first(recipes: dict[str, list[dict]]) -> None:
    """결과물명과 파일명이 같은 '대표' 레시피를 앞으로(예: stick.json이 stick_from_bamboo보다 먼저)."""
    for result_id, variants in recipes.items():
        item_name = result_id.split(":")[-1]
        variants.sort(key=lambda r: (r["recipe_id"] != item_name, r["recipe_id"]))


def _collect_used_tags(*recipe_maps: dict[str, list[dict]]) -> set[str]:
    used: set[str] = set()
    for recipes in recipe_maps:
        for variants in recipes.values():
            for entry in variants:
                slots = list(entry.get("key", {}).values()) + entry.get("ingredients", [])
                if entry.get("ingredient"):
                    slots.append(entry["ingredient"])
                for ing in slots:
                    if ing and ing.get("tag"):
                        used.add(ing["tag"])
    return used


def main() -> int:
    parser = argparse.ArgumentParser(description="MC jar에서 레시피를 추출해 recipes.json 생성")
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR, help=f"MC merged jar 경로 (기본: {DEFAULT_JAR})")
    parser.add_argument("--out", type=Path, default=OUTPUT_PATH, help=f"출력 경로 (기본: {OUTPUT_PATH})")
    args = parser.parse_args()

    if not args.jar.exists():
        print(f"[오류] jar를 찾을 수 없습니다: {args.jar}", file=sys.stderr)
        print("  Fabric 모드를 한 번 빌드(./gradlew build)하면 loom 캐시에 받아집니다.", file=sys.stderr)
        return 1

    print(f"[1/2] 추출: {args.jar}")
    data = extract(args.jar)
    counts = data["_meta"]["type_counts"]
    print(f"      shaped={counts['shaped']} shapeless={counts['shapeless']} "
          f"cooking={counts['cooking']} stonecutting={counts['stonecutting']} "
          f"mining={counts['mining']} tags={len(data['tags'])}")

    print(f"[2/2] 저장: {args.out}")
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

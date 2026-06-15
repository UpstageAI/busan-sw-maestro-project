"""게임 jar에서 추출한 제작 레시피(recipes.json) 로더.

데이터는 `scripts/extract_recipes.py`가 MC jar에서 굽는다(읽기전용·고정).
아이템 ID(`minecraft:iron_pickaxe`) 기준이며, 한 결과물에 레시피가 여럿이면
대표(파일명=결과물명)가 리스트 맨 앞에 온다.

부족 자원 계산·검증은 [facts](facts.py) 엔진(#2)이 이 구조를 사용한다.
"""
import json
from pathlib import Path

_DATA = json.loads((Path(__file__).resolve().parent / "recipes.json").read_text(encoding="utf-8"))

SHAPED: dict[str, list[dict]] = _DATA["shaped"]          # {item_id: [{pattern, key, reqs, result_count, recipe_id}]}
SHAPELESS: dict[str, list[dict]] = _DATA["shapeless"]    # {item_id: [{ingredients, reqs, result_count, recipe_id}]}
COOKING: dict[str, list[dict]] = _DATA["cooking"]        # {item_id: [{ingredient, method, recipe_id}]}
STONECUTTING: dict[str, list[dict]] = _DATA["stonecutting"]
MINING: dict[str, int] = _DATA["mining"]                # {block_id: 최소 곡괭이 레벨} (레벨 0 블록은 미수록)
TAGS: dict[str, list[str]] = _DATA["tags"]              # {tag_id: [item_id...]} (레시피에서 참조된 태그만)


def craft_recipes(item_id: str) -> list[dict]:
    """작업대 제작(shaped+shapeless) 레시피 목록. 대표 레시피가 앞에 온다."""
    return SHAPED.get(item_id, []) + SHAPELESS.get(item_id, [])


def cooking_recipes(item_id: str) -> list[dict]:
    """가열(화로/용광로/훈연/모닥불) 레시피 목록."""
    return COOKING.get(item_id, [])


def tag_members(tag_id: str) -> list[str]:
    """아이템 태그에 속한 아이템 ID 목록(예: minecraft:planks → 참나무 판자 등)."""
    return TAGS.get(tag_id, [])


def is_craftable(item_id: str) -> bool:
    return item_id in SHAPED or item_id in SHAPELESS


def is_tag(token: str) -> bool:
    """레시피 재료 토큰이 (구체 아이템이 아니라) 태그인지."""
    return token in TAGS


def block_mining_level(block_id: str) -> int:
    """블록 채굴에 필요한 최소 곡괭이 레벨(0=나무·금 곡괭이로 가능)."""
    return MINING.get(block_id, 0)


def recipe_grid(item_id: str) -> dict | None:
    """shaped 제작법을 3×3(9칸) 격자로 정규화해 반환한다(없으면 None).

    `pattern`(행 문자열)과 `key`(심볼→재료)를 좌상단 정렬로 9칸 리스트에 배치한다.
    각 칸은 구체 아이템 ID 또는 None(빈 칸). 태그 재료는 대표 구체 아이템(key의 item)으로
    렌더링한다(모드는 태그를 그릴 수 없음). shaped가 아니면(배치 의미 없음) None.

    반환: {"output": item_id, "count": 결과 개수, "grid": [9칸의 item_id|None]}
    """
    shaped = SHAPED.get(item_id)
    if not shaped:
        return None
    r = shaped[0]  # 대표 레시피(파일명=결과물명)가 앞에 온다
    key = r.get("key", {})
    grid: list[str | None] = [None] * 9
    for row_i, row in enumerate(r.get("pattern", [])[:3]):
        for col_i, ch in enumerate(row[:3]):
            if ch == " ":
                continue
            cell = key.get(ch)
            if cell:
                grid[row_i * 3 + col_i] = cell.get("item")
    return {"output": item_id, "count": r.get("result_count", 1), "grid": grid}

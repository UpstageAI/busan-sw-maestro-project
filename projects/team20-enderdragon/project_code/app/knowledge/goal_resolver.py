"""사용자 질문에서 제작 목표 아이템을 해석한다 (한국어명 → minecraft item id).

결정론 플래너(plan_materials)는 item id가 필요하므로, "철 곡괭이 만들래" 같은 질문에서
목표 아이템을 집어낸다. 제작 가능한 아이템만 후보로 둬 광물·원석 등은 목표로 잡지 않는다.

LLM 기반의 막연형 목표 제안(상태 보고 다음 목표 추천)은 후속 작업이며, 여기서는
명시적으로 언급된 제작 목표만 다룬다.
"""
from app.knowledge.minecraft_facts import ITEM_ID_TO_KO
from app.knowledge import recipes

# 한국어명 → item id (제작 가능한 아이템만)
_KO_TO_ID: dict[str, str] = {
    ko: item_id for item_id, ko in ITEM_ID_TO_KO.items() if recipes.is_craftable(item_id)
}


def resolve_craft_target(query: str) -> str | None:
    """질문에 언급된 제작 목표 아이템의 item id. 없으면 None.

    질문에 가장 먼저 등장한 아이템을 목표로 본다(예: "철 곡괭이 만들려면 돌 곡괭이가…"
    → 철 곡괭이). 같은 위치면 더 긴 이름을 택한다.
    """
    best_pos: tuple[int, int] | None = None
    best_id: str | None = None
    for ko, item_id in _KO_TO_ID.items():
        idx = query.find(ko)
        if idx == -1:
            continue
        key = (idx, -len(ko))  # 더 앞, 더 긴 이름 우선
        if best_pos is None or key < best_pos:
            best_pos = key
            best_id = item_id
    return best_id

"""질문에서 마인크래프트 확정 사실(채굴 티어·레시피)을 조회한다."""
from app.knowledge.minecraft_facts import (
    MINING_REQ,
    LEVEL_PHRASE,
    RECIPES,
    ACQUIRE,
    ALIASES,
)


def _terms(query: str, keywords: list[str]) -> set[str]:
    """질문과 키워드를 토큰화하고 별칭을 표준 키로 확장한다."""
    terms: set[str] = set()
    for raw in list(keywords) + query.split():
        t = raw.strip()
        if not t:
            continue
        terms.add(t)
        if t in ALIASES:
            terms.add(ALIASES[t])
    return terms


def lookup_facts(
    query: str,
    keywords: list[str],
    inventory_items: list[str] | None = None,
) -> list[str]:
    """질문에 해당하는 확정 사실 문장 리스트를 반환한다.

    inventory_items: 인벤토리 아이템 한국어명 목록. 보유 재료가 사용되는 레시피도 조회한다.
    매칭되는 사실이 없으면 빈 리스트(기존 위키 기반 답변 유지).
    """
    terms = _terms(query, keywords)
    # 인벤토리 한국어명을 terms에 추가해 보유 아이템이 재료인 레시피까지 매칭
    for item_name in (inventory_items or []):
        terms.add(item_name)

    facts: list[str] = []

    # 1) 채굴 티어
    for ore, req in MINING_REQ.items():
        if ore in terms or ore in query:
            facts.append(f"{ore}: {LEVEL_PHRASE[req]}")

    # 2) 제작 레시피 — 아이템명 직접 언급 또는 재료로 보유 중인 경우 모두 포함
    surfaced_recipes: list[str] = []
    for item, recipe in RECIPES.items():
        if item in terms or item in query or any(inv in recipe for inv in (inventory_items or [])):
            facts.append(f"{item}: {recipe}")
            surfaced_recipes.append(recipe)

    # 3) 획득/가공 — 직접 언급되었거나, 위 레시피의 '재료'로 등장한 중간재
    #    (예: 가위 질문 → 재료 '철 주괴'의 획득법까지 주입해 "돌→철주괴" 날조 차단)
    for item, how in ACQUIRE.items():
        if item in terms or item in query or any(item in r for r in surfaced_recipes):
            facts.append(f"{item}: {how}")

    return facts

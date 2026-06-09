from app.schemas import AgentState
from app.vector_store import search_documents
from app.knowledge.facts import lookup_facts
from app.knowledge.minecraft_facts import item_ko


def _inv_ko(inventory: list[dict]) -> list[str]:
    """인벤토리 아이템 ID 목록을 한국어명 리스트로 변환한다."""
    return [item_ko(i.get("item", "")) for i in inventory]


def retrieve_context(state: AgentState) -> dict:
    """Qdrant 위키 검색 + 확정 사실(채굴 티어·레시피)을 함께 조회한다."""
    query = state["query"]
    keywords = state.get("query_analysis", {}).get("keywords", [])
    inventory = state.get("inventory", [])

    search_query = f"{query} {' '.join(keywords)}" if keywords else query

    # 인벤토리가 있을 때 한국어 아이템명으로 검색 보강 (최대 5개)
    inv_names = _inv_ko(inventory)
    if inv_names:
        search_query = f"{search_query} {' '.join(inv_names[:5])} 제작법 레시피"

    return {
        "search_results": search_documents(query=search_query, n_results=5),
        "structured_facts": lookup_facts(query, keywords, inventory_items=inv_names),
    }

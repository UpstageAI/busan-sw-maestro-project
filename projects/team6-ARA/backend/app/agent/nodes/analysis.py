"""분석 노드 - /run 에 전달된 6-1 Item 통과.

비정형 텍스트 -> 분해/분류/추출은 POST /analyze/ 에서 수행한다. /run 그래프의
analysis_node 는 이미 분석된 Item 배열을 6-2 로 넘기는 연결부다.
raw_input 직접 분석은 향후 /run 단일 호출 흐름이 필요할 때 연결한다.
"""

from app.logging_config import get_logger, summarize_items

logger = get_logger("node.analysis")


def analysis_node(state: dict) -> dict:
    items = state.get("items", [])
    raw_input = state.get("raw_input")
    if raw_input and not items:
        logger.warning(
            "analysis_node: raw_input 직접 분석은 /run 에 연결되지 않음 -> 빈 items"
        )
        return {"items": []}
    logger.info("analysis_node: 항목 입력 통과 - %s", summarize_items(items))
    return {"items": items}

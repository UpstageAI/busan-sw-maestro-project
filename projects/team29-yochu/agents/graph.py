"""레시피 추천 멀티 에이전트 LangGraph 워크플로."""

import json
import os

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from openai import OpenAI

from agents.agent2.node import analyze_context
from agents.agent1.service import analyze_ingredients
from agents.agent4.schema import CandidateFood
from agents.agent3.node import route_cuisine
from agents.agent4.service import route_recipe_node
from agents.agent5.service import generate_recipe
from agents.schemas import AgentState

load_dotenv(encoding="utf-8-sig")

SOLAR_BASE_URL = (
    os.getenv("SOLAR_BASE_URL")
    or os.getenv("UPSTAGE_BASE_URL")
    or "https://api.upstage.ai/v1"
)
SOLAR_MODEL = os.getenv("SOLAR_MODEL") or os.getenv("UPSTAGE_MODEL") or "solar-mini"
TEST_API_KEYS = {"", "test", "dummy", "your_upstage_api_key_here"}


def _unique_items(items) -> list[str]:
    unique: list[str] = []
    for item in items or []:
        value = " ".join(str(item).strip().split())
        if value and value not in unique:
            unique.append(value)
    return unique


def _plain_mapping(value) -> dict:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


def _recipe_type(state: AgentState) -> str:
    recipe_type = state.get("recipe_type") or "korean"
    if recipe_type in {"korean", "chinese", "japanese", "western"}:
        return recipe_type
    return "korean"


def _food_directions(state: AgentState) -> dict:
    return _plain_mapping(state.get("food_directions"))


def _preferred_method(state: AgentState) -> str:
    return str(_food_directions(state).get("preferred_cooking_method") or "").strip()


def _time_limit_minutes(state: AgentState) -> int | None:
    value = _food_directions(state).get("cooking_time_limit_minutes")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _ingredient_groups(state: AgentState) -> dict[str, list[str]]:
    info = _plain_mapping(state.get("ingredient_info"))
    available = _unique_items(
        state.get("available_ingredients") or state.get("user_input_ingredients") or []
    )
    seasonings = _unique_items(info.get("seasonings", []))
    cookable = [item for item in available if item not in seasonings]
    main = _unique_items(info.get("main_ingredients", [])) or cookable[:1]
    sub = _unique_items(info.get("sub_ingredients", []))

    return {
        "available": available,
        "cookable": cookable,
        "main": [item for item in main if item in available],
        "sub": [item for item in sub if item in available],
        "seasonings": [item for item in seasonings if item in available],
        "carbohydrates": [
            item for item in _unique_items(info.get("carbohydrates", [])) if item in available
        ],
        "proteins": [
            item for item in _unique_items(info.get("proteins", [])) if item in available
        ],
        "vegetables": [
            item for item in _unique_items(info.get("vegetables", [])) if item in available
        ],
    }


def _candidate(
    name: str,
    recipe_type: str,
    required: list[str],
    optional: list[str],
    seasonings: list[str],
    methods: list[str],
    reason: str,
    *,
    cooking_time_minutes: int = 15,
) -> dict:
    required = _unique_items(required)
    optional = [item for item in _unique_items(optional) if item not in required]
    return {
        "name": name,
        "recipe_type": recipe_type,
        "required_ingredients": required,
        "optional_ingredients": optional,
        "seasonings": _unique_items(seasonings)[:4],
        "substitutions": {item: None for item in optional},
        "difficulty": "easy",
        "cooking_time_minutes": cooking_time_minutes,
        "taste_profile": ["savory"],
        "cooking_methods": _unique_items(methods),
        "reason": reason,
    }


def _simple_recipe_name(ingredients: list[str]) -> str:
    if not ingredients:
        return "간단한 재료 한 접시"
    return f"간단한 {' '.join(ingredients[:3])}"


def _get_solar_api_key() -> str:
    return (os.getenv("SOLAR_API_KEY") or os.getenv("UPSTAGE_API_KEY") or "").strip()


def _should_call_solar() -> bool:
    return _get_solar_api_key().lower() not in TEST_API_KEYS


def _extract_json(content: str) -> dict:
    cleaned = (content or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    return json.loads(cleaned)


def _ai_candidate_payload(state: AgentState, groups: dict[str, list[str]]) -> dict:
    return {
        "available_ingredients": groups["available"],
        "cookable_ingredients": groups["cookable"],
        "main_ingredients": groups["main"],
        "sub_ingredients": groups["sub"],
        "seasonings": groups["seasonings"],
        "recipe_type": _recipe_type(state),
        "food_directions": _food_directions(state),
        "user_mood_input": state.get("user_mood_input", ""),
        "user_situation_input": state.get("user_situation_input", ""),
    }


def _normalize_ai_candidate(candidate: dict, state: AgentState, groups: dict[str, list[str]]) -> dict | None:
    available = set(groups["available"])
    recipe_type = _recipe_type(state)
    required = [
        item
        for item in _unique_items(candidate.get("required_ingredients", []))
        if item in available
    ]
    optional = [
        item
        for item in _unique_items(candidate.get("optional_ingredients", []))
        if item in available and item not in required
    ]
    seasonings = [
        item
        for item in _unique_items(candidate.get("seasonings", []))
        if item in available
    ]

    if not required:
        required = (groups["main"] or groups["cookable"])[:1]
    if not required:
        return None

    normalized = {
        "name": str(candidate.get("name") or _simple_recipe_name(required)).strip(),
        "recipe_type": recipe_type,
        "required_ingredients": required,
        "optional_ingredients": optional,
        "seasonings": seasonings,
        "substitutions": {
            item: None for item in optional
        },
        "difficulty": candidate.get("difficulty") or "easy",
        "cooking_time_minutes": candidate.get("cooking_time_minutes") or 15,
        "taste_profile": _unique_items(candidate.get("taste_profile", ["savory"])),
        "cooking_methods": _unique_items(candidate.get("cooking_methods", ["간편 조리"])),
        "reason": candidate.get("reason") or "Solar AI가 현재 재료와 상황을 바탕으로 생성한 후보입니다.",
    }

    try:
        return CandidateFood.model_validate(normalized).model_dump()
    except Exception:
        return None


def _recipe_response_to_candidate(response: dict) -> dict | None:
    recipe_name = response.get("recipe_name") or response.get("name")
    ingredients = response.get("ingredients", [])
    if not recipe_name or not isinstance(ingredients, list):
        return None

    required: list[str] = []
    optional: list[str] = []
    seasonings: list[str] = []

    for ingredient in ingredients:
        if isinstance(ingredient, str):
            optional.append(ingredient)
            continue
        if not isinstance(ingredient, dict):
            continue

        name = str(ingredient.get("name") or "").strip()
        role = str(ingredient.get("role") or "").strip().lower()
        if not name:
            continue
        if role in {"main", "required", "protein"}:
            required.append(name)
        elif role in {"seasoning", "sauce"}:
            seasonings.append(name)
        else:
            optional.append(name)

    return {
        "name": recipe_name,
        "required_ingredients": required,
        "optional_ingredients": optional,
        "seasonings": seasonings,
        "difficulty": "easy",
        "cooking_time_minutes": (
            response.get("cook_time_minutes")
            or response.get("total_time_minutes")
            or response.get("cooking_time_minutes")
            or 15
        ),
        "taste_profile": ["savory"],
        "cooking_methods": ["AI 추천", "간편 조리"],
        "reason": response.get("description") or "Solar AI가 생성한 레시피 후보입니다.",
    }


def _raw_ai_candidates(parsed: dict) -> list[dict]:
    candidate_foods = parsed.get("candidate_foods")
    if isinstance(candidate_foods, list):
        return [
            candidate for candidate in candidate_foods if isinstance(candidate, dict)
        ]

    recipe_candidate = _recipe_response_to_candidate(parsed)
    return [recipe_candidate] if recipe_candidate else []


def _build_ai_agent4_candidates(state: AgentState, groups: dict[str, list[str]]) -> list[dict]:
    if not _should_call_solar():
        return []

    client = OpenAI(
        api_key=_get_solar_api_key(),
        base_url=SOLAR_BASE_URL,
    )
    payload = _ai_candidate_payload(state, groups)
    response = client.chat.completions.create(
        model=SOLAR_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 레시피 후보 생성 에이전트입니다. "
                    "현재 보유 재료와 사용자의 기분/상황을 바탕으로 Agent4가 평가할 수 있는 "
                    "요리 후보 3개를 생성하세요. 조리 순서나 완성 레시피를 쓰지 마세요. "
                    "반드시 JSON만 반환하세요. 반환 형식은 "
                    "{\"candidate_foods\":[{\"name\":\"요리명\","
                    "\"recipe_type\":\"korean|chinese|japanese|western\","
                    "\"required_ingredients\":[],\"optional_ingredients\":[],"
                    "\"seasonings\":[],\"difficulty\":\"easy\","
                    "\"cooking_time_minutes\":15,\"taste_profile\":[],"
                    "\"cooking_methods\":[],\"reason\":\"추천 이유\"}]} 입니다. "
                    "required_ingredients, optional_ingredients, seasonings에는 "
                    "available_ingredients 안에 있는 재료만 사용하세요."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
            },
        ],
        temperature=0.5,
    )
    parsed = _extract_json(response.choices[0].message.content or "{}")
    raw_candidates = _raw_ai_candidates(parsed)
    candidates = []
    seen_names: set[str] = set()
    for raw_candidate in raw_candidates:
        if not isinstance(raw_candidate, dict):
            continue
        candidate = _normalize_ai_candidate(raw_candidate, state, groups)
        if not candidate or candidate["name"] in seen_names:
            continue
        seen_names.add(candidate["name"])
        candidates.append(candidate)

    return candidates


def _build_rule_based_agent4_candidates(state: AgentState, groups: dict[str, list[str]]) -> list[dict]:
    """Fallback candidates when Solar candidate generation is unavailable."""

    recipe_type = _recipe_type(state)
    cookable = groups["cookable"]
    if not cookable:
        return []

    preferred_method = _preferred_method(state)
    time_limit = _time_limit_minutes(state)
    first_time = max(min(10, time_limit) if time_limit else 10, 1)
    common_methods = _unique_items(
        ["빠른 조리", "간편 조리", "팬 조리", "볶기", preferred_method]
    )
    main = groups["main"] or cookable[:1]
    optional = [item for item in [*groups["sub"], *groups["vegetables"]] if item not in main]
    base_materials = _unique_items([*main, *optional]) or cookable

    candidates = [
        _candidate(
            name=_simple_recipe_name(cookable),
            recipe_type=recipe_type,
            required=cookable,
            optional=[],
            seasonings=groups["seasonings"],
            methods=[*common_methods, "굽기", "끓이기", "삶기"],
            reason="현재 LangGraph state의 보유 재료만으로 바로 조리할 수 있는 후보입니다.",
            cooking_time_minutes=first_time,
        )
    ]

    if recipe_type == "korean":
        candidates.extend(
            [
                _candidate(
                    name=f"{main[0]}볶음",
                    recipe_type=recipe_type,
                    required=main,
                    optional=optional,
                    seasonings=groups["seasonings"],
                    methods=common_methods,
                    reason="주재료를 중심으로 한식 볶음 형태로 구성한 후보입니다.",
                    cooking_time_minutes=15,
                ),
                _candidate(
                    name=f"{main[0]}국",
                    recipe_type=recipe_type,
                    required=main[:1],
                    optional=optional,
                    seasonings=groups["seasonings"],
                    methods=["끓이기", "간편 조리", preferred_method],
                    reason="보유 재료를 국물 요리로 연결할 수 있는 후보입니다.",
                    cooking_time_minutes=18,
                ),
            ]
        )
    elif recipe_type == "japanese":
        candidates.append(
            _candidate(
                name=f"{main[0]}덮밥",
                recipe_type=recipe_type,
                required=base_materials[:2],
                optional=base_materials[2:],
                seasonings=groups["seasonings"],
                methods=["팬 조리", "조림", "간편 조리", preferred_method],
                reason="선택된 일식 스타일에 맞춰 덮밥 후보로 구성했습니다.",
                cooking_time_minutes=15,
            )
        )
    elif recipe_type == "chinese":
        candidates.append(
            _candidate(
                name=f"{main[0]}중식볶음",
                recipe_type=recipe_type,
                required=main,
                optional=optional,
                seasonings=groups["seasonings"],
                methods=[*common_methods, "강한 불 볶기"],
                reason="선택된 중식 스타일에 맞춰 볶음 후보로 구성했습니다.",
                cooking_time_minutes=15,
            )
        )
    else:
        candidates.append(
            _candidate(
                name=f"{main[0]}팬구이",
                recipe_type=recipe_type,
                required=main,
                optional=optional,
                seasonings=groups["seasonings"],
                methods=["팬 조리", "굽기", "간편 조리", preferred_method],
                reason="선택된 양식 스타일에 맞춰 팬 조리 후보로 구성했습니다.",
                cooking_time_minutes=15,
            )
        )

    while len(candidates) < 3:
        candidates.append(
            _candidate(
                name=f"{main[0]}간편요리 {len(candidates)}",
                recipe_type=recipe_type,
                required=main[:1],
                optional=[item for item in cookable if item not in main][:3],
                seasonings=groups["seasonings"],
                methods=common_methods,
                reason="agent4가 비교 평가할 수 있도록 보유 재료 기반으로 추가한 후보입니다.",
                cooking_time_minutes=12 + len(candidates),
            )
        )

    unique_candidates: list[dict] = []
    seen_names: set[str] = set()
    for candidate in candidates:
        if candidate["name"] in seen_names:
            continue
        seen_names.add(candidate["name"])
        unique_candidates.append(candidate)
    return unique_candidates


def _build_agent4_candidates(state: AgentState) -> list[dict]:
    """Build Agent4 candidates with Solar AI, falling back to rules."""

    groups = _ingredient_groups(state)
    if not groups["cookable"]:
        return []

    try:
        ai_candidates = _build_ai_agent4_candidates(state, groups)
    except Exception:
        ai_candidates = []

    if ai_candidates:
        return ai_candidates

    return _build_rule_based_agent4_candidates(state, groups)


def route_recipe(state: AgentState) -> dict:
    """Agent4 구현체를 LangGraph state에 연결한다."""

    agent4_state = dict(state)
    for field_name in ("ingredient_info", "food_directions"):
        field_value = agent4_state.get(field_name)
        if hasattr(field_value, "model_dump"):
            agent4_state[field_name] = field_value.model_dump()

    if not agent4_state.get("candidate_foods"):
        agent4_state["candidate_foods"] = _build_agent4_candidates(state)
    return route_recipe_node(agent4_state)


def route_after_ingredient_analyzer(state: AgentState) -> str:
    """재료 확인이 필요한 경우 다음 agent 실행을 멈춘다."""

    if state.get("vision_status") == "need_user_confirmation":
        return "wait_for_user_confirmation"

    return "continue"


def build_recipe_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("ingredient_analyzer", analyze_ingredients)
    workflow.add_node("context_analyzer", analyze_context)
    workflow.add_node("cuisine_router", route_cuisine)
    workflow.add_node("recipe_router", route_recipe)
    workflow.add_node("recipe_generator", generate_recipe)

    workflow.set_entry_point("ingredient_analyzer")
    workflow.add_conditional_edges(
        "ingredient_analyzer",
        route_after_ingredient_analyzer,
        {
            "continue": "context_analyzer",
            "wait_for_user_confirmation": END,
        },
    )
    workflow.add_edge("context_analyzer", "cuisine_router")
    workflow.add_edge("cuisine_router", "recipe_router")
    workflow.add_edge("recipe_router", "recipe_generator")
    workflow.add_edge("recipe_generator", END)

    return workflow.compile()


def run_recipe_graph(state: AgentState) -> AgentState:
    return build_recipe_graph().invoke(state)

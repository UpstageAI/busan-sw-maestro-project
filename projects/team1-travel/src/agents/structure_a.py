"""구조 A (baseline): LangGraph 정석 워크플로우.

초안(상세 기획서) 워크플로우를 반영한 7단계 흐름:

    1. parse_intent        : 자연어 요청 -> TravelIntent 구조화 
    2. classify_mode       : 참여자/출발지 해석 -> 추천 모드 판단
                             (single / group_single_origin / multi_origin)
    3. generate_candidates : 의미 기반 후보 관광지 선별 
    4. evaluate_fitness    : 후보별 적합도 0~10 점 평가 
    5. filter_constraints  : 예산·이동 등 제약 조건 필터링
    6. rank                : 적합도 기준 정렬 -> 상위 N 선별
    7. compose_response    : 선택 여행지의 상세 타임라인 생성 

LLM(Solar Pro) 은 parse_intent / generate_candidates / evaluate_fitness /
compose_response 의 4개 노드에 연동한다. 키가 없거나 호출에 실패하면 규칙 기반
폴백으로 동작해 그래프 자체는 항상 실행된다.
외부 도구: Upstage 임베딩(generate_candidates), OpenWeather(evaluate_fitness),
Kakao REST API(filter_constraints). (구조 B 는 본 프로젝트 범위 밖)
"""

from __future__ import annotations

from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src import config
from src.core.schemas import FitnessReport, SpotSelection, Timeline, TravelIntent
from src.prompts.templates import (
    build_clarification_messages,
    build_generate_and_score_messages,
    build_intent_messages,
    build_timeline_messages,
    render_timeline,
)
from src.tools.embeddings import get_top_k_spots
from src.tools.kakao_map import geocode, haversine, parse_radius_km, search_restaurants
from src.tools.weather import get_region_weather

# --- 추천 모드 상수  ---
MODE_SINGLE = "single"                             # 1명
MODE_GROUP_SINGLE_ORIGIN = "group_single_origin"   # 여러 명, 같은 출발지
MODE_MULTI_ORIGIN = "multi_origin"                 # 여러 명, 서로 다른 출발지

# --- LLM 설정 ---
MODEL_NAME = "solar-pro"  # Upstage Solar Pro (필요 시 모델명 교체)
TOP_K = 3                 # 최종 추천 개수


class AgentState(TypedDict, total=False):
    """그래프 노드 간 전달되는 상태."""

    user_query: str
    allow_clarification: bool      # False 이면 역질문 건너뜀 (두 번째 실행 시 사용)
    intent: Optional[TravelIntent]
    needs_clarification: bool
    clarification_question: str
    participant_mode: str
    candidates: List[dict]
    scored: List[dict]
    filtered: List[dict]
    ranked: List[dict]
    timeline: Optional[Timeline]
    response: str


# --- LLM 핸들 (지연 초기화) ---
_llm_cache: dict = {}


def get_llm(temperature: float = 0.0):
    """ChatUpstage(Solar Pro) 인스턴스를 지연 생성/캐시해 반환한다.

    키 미설정 시 EnvironmentError 를 던지며, 호출부에서 폴백 처리한다.
    """
    if temperature not in _llm_cache:
        from langchain_upstage import ChatUpstage

        config.validate_keys()
        _llm_cache[temperature] = ChatUpstage(
            model=MODEL_NAME, temperature=temperature
        )
    return _llm_cache[temperature]


# --- Node 1: 의도 파싱 + 조건 추출  ---
def parse_intent(state: AgentState) -> AgentState:
    """자연어 요청을 TravelIntent 로 구조화한다. """
    query = state.get("user_query", "")
    try:
        llm = get_llm(temperature=0.0)
        structured = llm.with_structured_output(TravelIntent)
        intent = structured.invoke(build_intent_messages(query))
    except Exception:
        # 폴백: 키 미설정/호출 실패 시 빈 의도로 초기화
        intent = TravelIntent()
    state["intent"] = intent
    return state


# --- Node 2: 정보 충분성 확인 + 역질문 생성 ---
def check_sufficiency(state: AgentState) -> AgentState:
    """의도 정보가 충분한지 판단하고, 부족하면 LLM으로 역질문 1개를 생성한다."""
    intent = state.get("intent") or TravelIntent()

    # allow_clarification=False 이면 역질문 없이 바로 통과 (두 번째 실행)
    if not state.get("allow_clarification", True):
        state["needs_clarification"] = False
        state["clarification_question"] = ""
        return state

    # 충분성 판정: 분위기 키워드와 선호 지역이 모두 없으면 부족
    sufficient = bool(intent.mood_keywords) or bool(intent.location_preference)

    if sufficient:
        state["needs_clarification"] = False
        state["clarification_question"] = ""
        return state

    state["needs_clarification"] = True
    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke(build_clarification_messages(intent.model_dump_json(indent=2)))
        state["clarification_question"] = response.content.strip()
    except Exception:
        state["clarification_question"] = "여행 분위기나 선호 지역을 조금 더 알려주시겠어요?"
    return state


def route_after_sufficiency(state: AgentState) -> str:
    """역질문 필요 시 END, 아니면 추천 파이프라인 진입."""
    return "clarify" if state.get("needs_clarification") else "recommend"


# --- Node 4: 참여자/출발지 -> 추천 모드 판단 ---
def classify_mode(state: AgentState) -> AgentState:
    """인원/출발지 정보로 추천 모드를 판단한다. (규칙 기반)

    origins 리스트에 2개 이상 출발지가 있으면 multi_origin 으로 분류.
    """
    intent = state.get("intent") or TravelIntent()
    if len(intent.origins) > 1:
        state["participant_mode"] = MODE_MULTI_ORIGIN
    elif intent.human_count <= 1:
        state["participant_mode"] = MODE_SINGLE
    else:
        state["participant_mode"] = MODE_GROUP_SINGLE_ORIGIN
    return state


# --- Node 5+6 통합: 후보 선별 + 적합도 평가 (LLM 1회, 날씨 병렬) ---
def generate_and_score(state: AgentState) -> AgentState:
    """임베딩 RAG + 날씨 병렬 조회 + LLM 1회로 후보 선별과 적합도 평가를 동시에 처리한다."""
    from concurrent.futures import ThreadPoolExecutor
    from src.core.mock_data import TOURIST_SPOTS

    intent = state.get("intent") or TravelIntent()
    user_query = state.get("user_query", "")

    # 1단계: Upstage 임베딩으로 상위 15개 추출
    pool = get_top_k_spots(user_query, TOURIST_SPOTS, k=15)

    # 2단계: 날씨 병렬 조회
    target_date = intent.start_date
    weather_ctx: dict[str, dict] = {}

    def fetch_weather(spot: dict) -> tuple[str, dict]:
        return spot["name"], get_region_weather(spot.get("region", ""), target_date)

    with ThreadPoolExecutor(max_workers=min(len(pool), 10)) as executor:
        for name, w in executor.map(fetch_weather, pool):
            if w:
                weather_ctx[name] = w

    # 3단계: LLM 1회로 선별 + 점수 평가
    def rule_score(spot: dict) -> int:
        s = 0
        text = " ".join(spot.get("mood", [])) + " " + spot.get("type", "")
        for kw in intent.mood_keywords:
            if kw and kw in text:
                s += 2
        if intent.participant_type in spot.get("best_for", []):
            s += 3
        return s

    try:
        llm = get_llm(temperature=0.0)
        structured = llm.with_structured_output(FitnessReport)
        messages = build_generate_and_score_messages(
            intent.model_dump_json(indent=2),
            pool,
            weather_ctx or None,
        )
        report = structured.invoke(messages)
        by_name = {e.name: e for e in report.evaluations}
        scored = [
            {**spot, "fitness_score": ev.score, "fitness_reason": ev.reason}
            for spot in pool
            if (ev := by_name.get(spot["name"]))
        ]
        if not scored:
            raise ValueError("LLM 선별 결과 없음")
    except Exception:
        scored = [
            {**spot, "fitness_score": rule_score(spot), "fitness_reason": ""}
            for spot in pool
        ]

    state["candidates"] = pool
    state["scored"] = scored
    return state


# --- Node 7: 제약 필터링 ---
def filter_constraints(state: AgentState) -> AgentState:
    """이동 반경(Kakao 지오코딩 + 하버사인)과 예산(cost_level)으로 후보를 필터링한다."""
    from src.tools.region_coords import CITY_TO_REGION, REGION_COORDS

    intent = state.get("intent") or TravelIntent()
    scored = state.get("scored", [])

    # --- 이동 반경 필터 ---
    radius_km = parse_radius_km(intent.travel_radius)
    origin_coords: tuple[float, float] | None = None
    if radius_km is not None and intent.origin:
        # 1순위: Kakao API 지오코딩, 2순위: 광역 지역 직접 조회, 3순위: 구/동 → 광역 매핑
        origin_coords = (
            geocode(intent.origin)
            or REGION_COORDS.get(intent.origin)
            or REGION_COORDS.get(CITY_TO_REGION.get(intent.origin, ""))
        )

    def within_radius(spot: dict) -> bool:
        if radius_km is None or origin_coords is None:
            return True
        region = spot.get("region", "")
        dest_coords = REGION_COORDS.get(region)
        if dest_coords is None:
            return True
        dist = haversine(origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1])
        return dist <= radius_km

    # --- 예산 필터 ---
    BUDGET_ALLOW: dict[str, set[str]] = {
        "low": {"low"},
        "mid": {"low", "mid"},
        "high": {"low", "mid", "high"},
    }
    allowed_costs = BUDGET_ALLOW.get(intent.budget_level or "high", {"low", "mid", "high"})

    def within_budget(spot: dict) -> bool:
        cost = spot.get("cost_level", "mid")
        return cost in allowed_costs

    filtered = [s for s in scored if within_radius(s) and within_budget(s)]
    # 필터 후 결과가 없으면 안전망: 전체 통과
    state["filtered"] = filtered if filtered else scored
    return state


# --- Node 6: 랭킹 ---
def rank(state: AgentState) -> AgentState:
    """적합도 점수 기준으로 정렬해 상위 N개를 선별한다. """

    filtered = state.get("filtered", [])
    ranked = sorted(
        filtered, key=lambda s: s.get("fitness_score", 0), reverse=True
    )
    state["ranked"] = ranked[:TOP_K]
    return state


# --- Node 7: 타임라인 생성 (Solar Pro) ---
def compose_response(state: AgentState) -> AgentState:
    """선택(최상위) 여행지에 대한 상세 타임라인을 생성한다."""
    intent = state.get("intent") or TravelIntent()
    ranked = state.get("ranked", [])

    # reject 의도면 LLM 호출 없이 즉시 안내
    if intent.intent_type == "reject":
        state["response"] = "여행 추천 요청으로 보기 어려워요. 원하는 여행을 알려 주세요."
        return state

    # 랭킹 1위를 일정 대상 여행지로 선택 (싱글턴)
    destination = ranked[0].get("name", "추천 여행지") if ranked else "추천 여행지"

    # 관광지 이름 + 광역 지역명으로 주변 맛집+카페 검색 (실패 시 빈 리스트)
    region = ranked[0].get("region", "") if ranked else ""
    restaurants = search_restaurants(destination, region=region, k=5)

    try:
        llm = get_llm(temperature=0.3)
        intent_text = intent.model_dump_json(indent=2)
        structured = llm.with_structured_output(Timeline)
        messages = build_timeline_messages(intent_text, destination, ranked, restaurants)
        timeline = structured.invoke(messages)
        state["timeline"] = timeline
        state["response"] = render_timeline(timeline)
    except Exception:
        # 폴백: 키 미설정/호출 실패 시 후보명만 나열
        names = ", ".join(s.get("name", "?") for s in ranked) or "추천 결과 없음"
        state["response"] = f"추천 여행지: {names}"
    return state


# --- 조건부 라우팅: reject 면 추천 파이프라인을 건너뛴다 ---
def route_after_intent(state: AgentState) -> str:
    """parse_intent 결과로 분기. reject 면 후보/평가 노드를 모두 건너뛴다."""
    intent = state.get("intent") or TravelIntent()
    return "reject" if intent.intent_type == "reject" else "recommend"


def build_graph():
    """구조 A 워크플로우 그래프를 컴파일해 반환한다."""
    config.setup_langsmith()  # LangSmith 관측성 환경변수 주입

    graph = StateGraph(AgentState)

    graph.add_node("parse_intent", parse_intent)
    graph.add_node("check_sufficiency", check_sufficiency)
    graph.add_node("classify_mode", classify_mode)
    graph.add_node("generate_and_score", generate_and_score)
    graph.add_node("filter_constraints", filter_constraints)
    graph.add_node("rank", rank)
    graph.add_node("compose_response", compose_response)

    graph.set_entry_point("parse_intent")
    # reject → compose_response 직행, recommend → 충분성 확인
    graph.add_conditional_edges(
        "parse_intent",
        route_after_intent,
        {"reject": "compose_response", "recommend": "check_sufficiency"},
    )
    # 역질문 필요 시 END, 아니면 추천 파이프라인
    graph.add_conditional_edges(
        "check_sufficiency",
        route_after_sufficiency,
        {"clarify": END, "recommend": "classify_mode"},
    )
    graph.add_edge("classify_mode", "generate_and_score")
    graph.add_edge("generate_and_score", "filter_constraints")
    graph.add_edge("filter_constraints", "rank")
    graph.add_edge("rank", "compose_response")
    graph.add_edge("compose_response", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"user_query": "조용한 바다 보러 2박 3일 가고 싶어"})
    print(result.get("response"))

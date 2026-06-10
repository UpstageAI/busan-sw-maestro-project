"""시스템 프롬프트 · Few-shot · 메시지 빌더 관리.

구조 A 의 의도 파싱(parse_intent) 및 타임라인 생성(compose_response) 단계가
참조하는 프롬프트를 한 곳에서 관리한다. 프롬프트 '문구'와 '메시지 조립',
'출력 렌더링'을 이 모듈에 모아, 에이전트 노드(structure_a.py)는 빌더만 호출한다.
"""

from __future__ import annotations

import json
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

# ---------------------------------------------------------------------------
# 1. 의도 파싱 (parse_intent)
# ---------------------------------------------------------------------------

# --- 의도 파싱용 시스템 프롬프트 ---
INTENT_SYSTEM_PROMPT = """\
당신은 사용자의 자연어 여행 요청을 구조화된 JSON 으로 변환하는 추출기입니다.
반드시 TravelIntent 스키마(snake_case)에 맞춰 출력하세요.

[추출 대상]
- intent_type        : 여행 추천 요청이면 "travel_recommend", 아니면 "reject"
- location_preference: 선호 지역/목적지 (없으면 null)
- origin             : 출발지 (예: 서울, 부산. 없으면 null)
- origins            : 참여자들이 서로 다른 출발지에서 출발할 때 각 출발지를 리스트로 기입 (예: ["서울", "부산"]). 출발지가 하나이거나 불명확하면 빈 리스트 []
- travel_radius      : 이동 반경 (예: 근교, 전국, 100km 이내. 없으면 null)
- transport_mode     : 이동 수단 (예: 자가용, 대중교통, 기차. 없으면 null)
- duration_nights    : 숙박 일수 (당일치기=0, 불명확하면 null)
- start_date         : 출발 희망일 YYYY-MM-DD (없으면 null)
- human_count        : 총 인원 수 (불명확하면 1)
- participant_type   : 동행자 유형 (solo / couple / friends / family)
- constraints        : 예산·이동·시간 등 제약 표현 리스트
- mood_keywords      : 분위기/무드/개인취향 키워드 리스트
- budget_level       : 예산 수준 (low / mid / high, 없으면 null)

[규칙]
- 여행 추천 요청이 아니면 intent_type 을 "reject" 로 설정합니다.
- 명시되지 않은 선택 필드는 null 로 둡니다.
- 인원수가 불명확하면 human_count=1, participant_type="solo" 로 둡니다.
- "친구랑 간다" 처럼 동행만 언급된 경우 동행자 유형만 추론하고,
  출발지가 다르다고 단정하지 않습니다. (출발지 분기는 별도 단계에서 판단)
- 근거 없는 값은 지어내지 말고 null/기본값을 사용합니다.
- 여러 참여자가 서로 다른 출발지에서 모인다고 명시된 경우에만 origins 에 각각 기입. 모호하면 빈 리스트.
"""

# --- 의도 파싱 Few-shot 예시 ---
INTENT_FEW_SHOT = [
    {
        "input": "서울에서 여자친구랑 자가용으로 2박 3일 조용한 바다 여행 가고 싶어, 예산은 넉넉해",
        "output": {
            "intent_type": "travel_recommend",
            "location_preference": None,
            "origin": "서울",
            "travel_radius": None,
            "transport_mode": "자가용",
            "duration_nights": 2,
            "start_date": None,
            "human_count": 2,
            "participant_type": "couple",
            "constraints": [],
            "mood_keywords": ["조용한", "바다"],
            "budget_level": "high",
        },
    },
    {
        "input": "부산 근교로 친구들이랑 대중교통 타고 1박 2일 활기차게 놀고 싶어",
        "output": {
            "intent_type": "travel_recommend",
            "location_preference": "부산",
            "origin": None,
            "travel_radius": "근교",
            "transport_mode": "대중교통",
            "duration_nights": 1,
            "start_date": None,
            "human_count": 3,
            "participant_type": "friends",
            "constraints": [],
            "mood_keywords": ["활기찬"],
            "budget_level": None,
        },
    },
    {
        "input": "오늘 날씨 어때?",
        "output": {
            "intent_type": "reject",
            "location_preference": None,
            "origin": None,
            "travel_radius": None,
            "transport_mode": None,
            "duration_nights": None,
            "start_date": None,
            "human_count": 1,
            "participant_type": "solo",
            "constraints": [],
            "mood_keywords": [],
            "budget_level": None,
        },
    },
]


def build_intent_messages(user_query: str) -> List[BaseMessage]:
    """의도 파싱용 메시지(시스템 + few-shot + 사용자 질의)를 조립한다."""
    messages: List[BaseMessage] = [SystemMessage(content=INTENT_SYSTEM_PROMPT)]
    for example in INTENT_FEW_SHOT:
        messages.append(HumanMessage(content=example["input"]))
        messages.append(
            AIMessage(content=json.dumps(example["output"], ensure_ascii=False))
        )
    messages.append(HumanMessage(content=user_query))
    return messages


# ---------------------------------------------------------------------------
# 2. 후보 선별 + 적합도 평가 통합 (generate_and_score) — LLM 호출 1회
# ---------------------------------------------------------------------------

GENERATE_AND_SCORE_SYSTEM_PROMPT = """\
당신은 국내 여행지 큐레이터 겸 적합도 평가자입니다.
사용자 의도와 후보 목록을 보고, 가장 잘 맞는 관광지를 선별하고 적합도를 한 번에 평가합니다.

[선별 기준]
- 단순 지역 일치가 아닌 무드·취향·동행자 적합도 고려
- 반드시 제공된 후보 목록 안의 이름만 사용합니다. (새로 지어내지 않음)
- 5~8곳을 선별합니다. 적절한 후보가 적으면 더 적게 가능.

[평가 기준]
- 무드/개인취향(mood_keywords) 일치도
- 동행자 유형(participant_type) 적합도
- 여행 기간·이동수단·예산 등 제약과의 부합도

[출력]
선별된 후보에 대해 name, score(0~10), reason(한 문장)을 evaluations 리스트(JSON)로 출력합니다.
"""

GENERATE_AND_SCORE_USER_TEMPLATE = """\
[사용자 의도]
{intent}

[후보 목록]
{spots}
{weather_section}
위 후보 중 의도에 맞는 관광지를 선별하고 적합도를 평가해 주세요.
"""


def build_generate_and_score_messages(
    intent_text: str,
    spots: List[dict],
    weather_ctx: dict | None = None,
) -> List[BaseMessage]:
    """후보 선별 + 적합도 평가 통합 메시지를 조립한다."""
    if weather_ctx:
        lines = [
            f"- {name}: {w.get('description','')}, {w.get('temp','')}°C, "
            f"강수확률 {int(w.get('rain_prob', 0) * 100)}%"
            for name, w in weather_ctx.items() if w
        ]
        weather_section = "\n[날씨 정보]\n" + "\n".join(lines) + "\n" if lines else ""
    else:
        weather_section = ""

    human = GENERATE_AND_SCORE_USER_TEMPLATE.format(
        intent=intent_text,
        spots=_format_spots(spots),
        weather_section=weather_section,
    )
    return [
        SystemMessage(content=GENERATE_AND_SCORE_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ]


# ---------------------------------------------------------------------------
# 3. 적합도 평가 (evaluate_fitness) — 초안 7.6
# ---------------------------------------------------------------------------

FITNESS_SYSTEM_PROMPT = """\
당신은 여행지 적합도 평가자입니다.
사용자 의도를 기준으로 각 후보 관광지의 적합도를 0~10 점으로 평가하세요.

[평가 기준]
- 무드/개인취향(mood_keywords) 일치도
- 동행자 유형(participant_type) 적합도
- 여행 기간·이동수단·예산 등 제약과의 부합도

[규칙]
- 제공된 후보 전부에 대해 name, score(0~10), reason(한 문장)을 출력합니다.
- 후보 목록에 없는 관광지는 평가하지 않습니다.
- evaluations 리스트(JSON)로만 출력합니다.
"""

FITNESS_USER_TEMPLATE = """\
[사용자 의도]
{intent}

[평가 대상 후보]
{spots}

각 후보의 적합도를 평가해 주세요.
"""


def build_fitness_messages(intent_text: str, spots: List[dict]) -> List[BaseMessage]:
    """적합도 평가용 메시지를 조립한다."""
    human = FITNESS_USER_TEMPLATE.format(
        intent=intent_text, spots=_format_spots(spots)
    )
    return [
        SystemMessage(content=FITNESS_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ]


def build_fitness_with_weather_messages(
    intent_text: str, spots: List[dict], weather_ctx: dict[str, dict]
) -> List[BaseMessage]:
    """날씨 컨텍스트를 포함한 적합도 평가용 메시지를 조립한다."""
    weather_lines = []
    for name, w in weather_ctx.items():
        if w:
            weather_lines.append(
                f"- {name}: {w.get('description','')}, {w.get('temp','')}°C, "
                f"강수확률 {int(w.get('rain_prob', 0) * 100)}%"
            )
    weather_section = (
        "\n[날씨 정보 (여행 일정 기준)]\n" + "\n".join(weather_lines)
        if weather_lines
        else ""
    )
    human = FITNESS_USER_TEMPLATE.format(
        intent=intent_text, spots=_format_spots(spots)
    ) + weather_section
    return [
        SystemMessage(content=FITNESS_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ]


# ---------------------------------------------------------------------------
# 4. 타임라인 생성 (compose_response)
# ---------------------------------------------------------------------------

# --- 타임라인 생성용 시스템 프롬프트 ---
TIMELINE_SYSTEM_PROMPT = """\
당신은 친절한 국내 여행 일정 플래너입니다.
사용자 의도와 선택된 여행지를 바탕으로 상세한 '타임라인' 일정을 작성하세요.

[출력 형식]
Timeline 스키마(JSON)에 맞춰 출력합니다.
- destination : 일정의 대상 여행지/지역
- items       : 시간순 일정 항목 리스트. 각 항목은 다음을 포함합니다.
    - time      : 시간 (예: 09:00, 09:00-10:30)
    - place     : 장소
    - activity  : 활동 (예: 카페 가기, 해변 산책)
    - transport : 해당 장소로의 이동 수단 (사용자의 transport_mode 반영)
    - cost      : 예상 비용 (예: 무료, 15,000원)

[작성 지침]
- 여행 기간(duration_nights)과 인원/동행자 유형에 맞춰 동선을 구성합니다.
- 이동 수단(transport_mode)이 있으면 transport 에 일관되게 반영합니다.
- 비용은 일반적인 추정 범위로만 적고, 정확한 가격을 단정하지 않습니다.
- 후보 목록에 없는 엉뚱한 장소를 만들지 않습니다.
- [실제 맛집/카페 목록]이 제공된 경우, 반드시 해당 목록에 있는 이름과 주소만 사용합니다.
  목록에 없는 식당·카페 이름은 절대 지어내지 않습니다. 목록이 충분하지 않으면
  식사 항목의 place를 "현지 식당 (목록 참고)" 처럼 표기합니다.
"""

# --- 타임라인 생성용 사용자 메시지 템플릿 ---
TIMELINE_USER_TEMPLATE = """\
[사용자 의도]
{intent}

[선택된 여행지]
{destination}

[참고 후보 관광지]
{spots}
{restaurants_section}
위 정보를 바탕으로 destination 에 대한 상세 타임라인을 작성해 주세요.
"""


def _format_spots(spots: List[dict]) -> str:
    """후보 관광지 리스트를 프롬프트용 JSON 문자열로 직렬화한다.

    LLM 입력 포맷을 의도(JSON)와 일관되게 맞추기 위해 JSON 으로 통일한다.
    """
    if not spots:
        return "[]"
    projected = [
        {
            "name": spot.get("name"),
            "region": spot.get("region"),
            "type": spot.get("type"),
            "mood": spot.get("mood", []),
            "best_for": spot.get("best_for", []),
        }
        for spot in spots
    ]
    return json.dumps(projected, ensure_ascii=False, indent=2)


def build_timeline_messages(
    intent_text: str,
    destination: str,
    spots: List[dict],
    restaurants: List[dict] | None = None,
) -> List[BaseMessage]:
    """타임라인 생성용 메시지(시스템 + 사용자 컨텍스트)를 조립한다."""
    if restaurants:
        lines = "\n".join(
            f"- {r['name']} ({r['address']}) — {r['category']}"
            for r in restaurants
        )
        restaurants_section = f"\n[실제 맛집 목록 (Kakao 검색 결과)]\n{lines}\n"
    else:
        restaurants_section = ""

    human = TIMELINE_USER_TEMPLATE.format(
        intent=intent_text,
        destination=destination,
        spots=_format_spots(spots),
        restaurants_section=restaurants_section,
    )
    return [
        SystemMessage(content=TIMELINE_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ]


# ---------------------------------------------------------------------------
# 5. 역질문 생성 (check_sufficiency)
# ---------------------------------------------------------------------------

CLARIFICATION_SYSTEM_PROMPT = """\
사용자가 여행 추천을 요청했으나 핵심 정보(분위기 또는 선호 지역)가 부족합니다.
자연스러운 한국어로 질문 한 문장만 생성하세요. 선택지를 포함하면 좋습니다.
예: "어떤 분위기의 여행을 원하세요? 조용한 바다, 활기찬 도시, 산속 힐링 중에서 알려주시면 더 잘 맞는 곳을 추천해 드릴게요."
JSON 이 아닌 평문 한 문장만 출력합니다.
"""


def build_clarification_messages(intent_text: str) -> List[BaseMessage]:
    """역질문 생성용 메시지를 조립한다."""
    return [
        SystemMessage(content=CLARIFICATION_SYSTEM_PROMPT),
        HumanMessage(content=f"[파싱된 의도]\n{intent_text}"),
    ]


def render_timeline(timeline) -> str:
    """Timeline 객체를 사용자 표시용 텍스트로 렌더링한다."""
    if not timeline or not getattr(timeline, "items", None):
        return "일정을 생성하지 못했습니다."
    lines = [f"🗺️ {timeline.destination} 추천 일정", ""]
    for item in timeline.items:
        extra = []
        if item.transport:
            extra.append(f"이동: {item.transport}")
        if item.cost:
            extra.append(f"비용: {item.cost}")
        suffix = f"  ({' · '.join(extra)})" if extra else ""
        lines.append(f"{item.time} | {item.place} — {item.activity}{suffix}")
    return "\n".join(lines)

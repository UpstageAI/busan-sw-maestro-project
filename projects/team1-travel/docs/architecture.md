# 자연어 여행지 추천 에이전트 — 아키텍처 문서

> **대상 브랜치:** `feature/sungyoon`  
> **작성일:** 2026-06-07  
> **스택:** Upstage Solar Pro · LangGraph · Streamlit · Kakao Local API · OpenWeather · Nominatim

---

## 1. 프로젝트 개요

사용자가 자연어로 여행 요청을 입력하면, LangGraph 워크플로우가 의도를 파싱하고 국내 관광지 50선에서 조건에 맞는 여행지를 추천한다. 최종적으로 실제 맛집·카페를 포함한 상세 타임라인을 생성한다.

```
사용자 자연어 입력
        ↓
  TravelIntent 구조화
        ↓
  정보 충분성 판단 ──── 부족 ──→ 역질문(채팅 버블) → 재입력 → 루프
        ↓ 충분
  참여자 모드 분류
        ↓
  임베딩 RAG + 날씨(병렬) + LLM 1회 → 선별 + 점수
        ↓
  반경·예산 필터링
        ↓
  TOP 3 카드 표시 → 사용자 선택
        ↓
  Kakao 맛집·카페 검색 + 타임라인 생성 → 일정 표시
```

---

## 2. 디렉터리 구조

```
asm-team1/
├── app/
│   └── main.py                  # Streamlit UI
├── src/
│   ├── agents/
│   │   └── structure_a.py       # LangGraph 그래프 정의 + 모든 노드 함수
│   ├── core/
│   │   ├── schemas.py           # Pydantic v2 스키마
│   │   └── mock_data.py         # 국내 관광지 50선 데이터
│   ├── prompts/
│   │   └── templates.py         # 시스템 프롬프트 + 메시지 빌더
│   ├── tools/
│   │   ├── embeddings.py        # Upstage 임베딩 RAG
│   │   ├── kakao_map.py         # Nominatim 지오코딩 + Kakao 맛집 검색
│   │   ├── weather.py           # OpenWeather 날씨 API
│   │   └── region_coords.py     # 광역 지역 좌표 + 구/동 → 광역 매핑
│   └── config.py                # 환경변수 로드 + LangSmith 설정
├── docs/
│   └── architecture.md          # 이 문서
├── tests/
│   └── test_queries.py          # 평가 쿼리 20선
└── .env                         # API 키 (git 제외)
```

---

## 3. LangGraph 워크플로우

### 3-1. 전체 그래프 흐름

```
                        ┌─────────────────┐
                        │   parse_intent  │  ← 진입점
                        └────────┬────────┘
                                 │
               ┌─────────────────┴─────────────────┐
          intent_type                          intent_type
          == "reject"                        == "travel_recommend"
               │                                     │
               ▼                                     ▼
      ┌────────────────┐                  ┌───────────────────┐
      │ compose_response│                 │ check_sufficiency │
      │  (안내 문구만)  │                  └─────────┬─────────┘
      └────────┬────────┘                           │
               │                     ┌──────────────┴──────────────┐
               │              needs_clarification           needs_clarification
               │                  == True                      == False
               │                     │                             │
               │                     ▼                             ▼
               │                   END                   ┌──────────────────┐
               │               (역질문 반환)               │  classify_mode   │
               │                                          └────────┬─────────┘
               │                                                   │
               │                                                   ▼
               │                                       ┌───────────────────────┐
               │                                       │  generate_and_score   │
               │                                       │  (임베딩+날씨+LLM 1회) │
               │                                       └────────────┬──────────┘
               │                                                    │
               │                                                    ▼
               │                                       ┌───────────────────────┐
               │                                       │  filter_constraints   │
               │                                       │  (반경 + 예산 필터)    │
               │                                       └────────────┬──────────┘
               │                                                    │
               │                                                    ▼
               │                                          ┌──────────────┐
               │                                          │     rank     │
               │                                          │  (TOP K 정렬) │
               │                                          └──────┬───────┘
               │                                                 │
               └─────────────────────────────────────────────────┤
                                                                  ▼
                                                     ┌────────────────────┐
                                                     │  compose_response  │
                                                     │  (맛집검색 + 타임라인)│
                                                     └──────────┬─────────┘
                                                                │
                                                               END
```

### 3-2. 분기 조건 상세

| 분기점 | 조건 | 목적지 |
|--------|------|--------|
| `parse_intent` 이후 | `intent_type == "reject"` | `compose_response` (안내 문구만 반환) |
| `parse_intent` 이후 | `intent_type == "travel_recommend"` | `check_sufficiency` |
| `check_sufficiency` 이후 | `mood_keywords` 비어 있고 `location_preference` 없음 | `END` (역질문 생성 후 종료) |
| `check_sufficiency` 이후 | 위 조건 외 | `classify_mode` → 추천 파이프라인 |
| `check_sufficiency` 이후 | `allow_clarification == False` (2차 실행) | 역질문 없이 강제 통과 |

---

## 4. 노드별 상세 설명

### Node 1: `parse_intent`

**목적:** 자연어 요청 → `TravelIntent` 구조화 출력  
**방식:** Solar Pro LLM + `with_structured_output(TravelIntent)`  
**폴백:** 키 없거나 호출 실패 → 빈 `TravelIntent()` 반환 (워크플로우 계속)

추출 필드:

| 필드 | 설명 | 예시 |
|------|------|------|
| `intent_type` | 여행 요청 여부 | `travel_recommend` / `reject` |
| `location_preference` | 선호 지역 | `강릉`, `제주` |
| `origin` | 출발지 | `서울`, `구로` |
| `origins` | 복수 출발지 (다른 지점) | `["서울", "부산"]` |
| `travel_radius` | 이동 반경 | `근교`, `50km 이내`, `전국` |
| `transport_mode` | 이동 수단 | `자가용`, `대중교통` |
| `duration_nights` | 숙박 일수 | `0`(당일), `1`(1박2일) |
| `start_date` | 출발일 | `2026-06-10` |
| `human_count` | 인원 수 | `3` |
| `participant_type` | 동행 유형 | `solo`, `couple`, `friends`, `family` |
| `mood_keywords` | 분위기 키워드 | `["조용한", "바다"]` |
| `budget_level` | 예산 수준 | `low`, `mid`, `high` |

---

### Node 2: `check_sufficiency`

**목적:** 정보 충분성 판단 → 부족하면 역질문 생성  
**충분성 판정 규칙:**

```python
sufficient = bool(intent.mood_keywords) or bool(intent.location_preference)
```

- `mood_keywords`가 있거나, `location_preference`가 있으면 → 충분 → `classify_mode` 진행
- 둘 다 없으면 → 부족 → LLM으로 역질문 1개 생성 → `END`

**역질문 폴백:** LLM 실패 시 고정 문구 `"여행 분위기나 선호 지역을 조금 더 알려주시겠어요?"`

**2차 실행 처리:** `allow_clarification=False` 플래그로 역질문 재발 방지

---

### Node 3: `classify_mode`

**목적:** 참여자/출발지 정보로 추천 모드 분류 (규칙 기반, LLM 없음)

| 조건 | 모드 |
|------|------|
| `origins` 리스트에 2개 이상 출발지 | `multi_origin` |
| `human_count <= 1` | `single` |
| 그 외 | `group_single_origin` |

---

### Node 4: `generate_and_score` _(통합 노드)_

**목적:** 후보 선별 + 적합도 평가를 LLM 1회로 처리 (기존 2단계 → 1단계로 최적화)

**실행 순서:**

```
1. Upstage 임베딩 RAG
   └─ solar-embedding-1-large-passage 로 관광지 50개 인코딩 (캐시)
   └─ solar-embedding-1-large-query 로 쿼리 인코딩
   └─ 코사인 유사도 상위 15개 추출

2. 날씨 병렬 조회 (ThreadPoolExecutor, 최대 10 스레드)
   └─ 각 후보의 광역 지역 좌표 → OpenWeather 5일 예보 API
   └─ 여행 출발일(start_date) 기준 12시 예보 반환
   └─ description / temp / rain_prob

3. Solar Pro LLM 1회 호출 (FitnessReport 구조화 출력)
   └─ 입력: TravelIntent JSON + 후보 15개 + 날씨 컨텍스트(있을 때)
   └─ 출력: 선별된 후보 각각의 name / score(0~10) / reason
```

**폴백:** LLM 실패 시 무드 키워드·참여자 유형 기반 규칙 점수 계산

---

### Node 5: `filter_constraints`

**목적:** 이동 반경 + 예산 수준으로 후보 필터링

**이동 반경 필터:**

```
출발지(origin) 좌표 결정 우선순위:
  1순위: Nominatim(OpenStreetMap) 지오코딩 → 실제 위경도
  2순위: REGION_COORDS 광역 지역 직접 조회 (예: "서울")
  3순위: CITY_TO_REGION 매핑 → 구/동 → 광역 지역 (예: "구로" → "서울")

travel_radius 파싱:
  "근교" → 150km
  "당일치기" → 100km
  "50km 이내" → 50.0km
  "전국" / null → 필터 없음

거리 계산: 하버사인 공식 (직선 거리)
```

**예산 필터:**

| budget_level | 허용 cost_level |
|--------------|----------------|
| `low` | low |
| `mid` | low, mid |
| `high` (기본값) | low, mid, high |

**안전망:** 필터 후 결과가 없으면 전체 통과 (0개 방지)

---

### Node 6: `rank`

**목적:** 적합도 점수 내림차순 정렬 → 상위 `TOP_K`(기본값 3)개 선별  
**방식:** 규칙 기반 정렬 (LLM 없음)

---

### Node 7: `compose_response`

**목적:** 사용자가 선택한 여행지의 상세 타임라인 + 실제 맛집·카페 생성

**실행 순서:**

```
1. Kakao Local API 맛집·카페 검색
   └─ 관광지 이름으로 FD6(음식점) 5개 검색: "{destination} 맛집"
   └─ 관광지 이름으로 CE7(카페) 2개 검색: "{destination} 카페"
   └─ 결과 부족 시 광역 지역명(region)으로 보완
   └─ 중복 제거 후 LLM에 전달

2. Solar Pro LLM (temperature=0.3, Timeline 구조화 출력)
   └─ 입력: TravelIntent + 선택 여행지 + 관광지 목록 + 실제 맛집 목록
   └─ 출력: destination / items[](time, place, activity, transport, cost)
   └─ 프롬프트 지침: 제공된 맛집 목록 외 이름 생성 금지
```

**폴백:** LLM 실패 시 후보명 나열 문자열 반환

> **주의:** `compose_response`는 그래프 실행 중에도 호출되지만, UI에서 사용자가 카드를 선택한 후 **그래프 재실행 없이** 직접 함수 호출로도 사용된다.

---

## 5. 데이터 흐름 (AgentState)

```
user_query (str)
    │
    ▼ parse_intent
intent (TravelIntent)
allow_clarification (bool)
    │
    ▼ check_sufficiency
needs_clarification (bool)
clarification_question (str)
    │
    ▼ classify_mode
participant_mode (str)        # "single" | "group_single_origin" | "multi_origin"
    │
    ▼ generate_and_score
candidates (List[dict])       # 임베딩 상위 15개
scored (List[dict])           # candidates + fitness_score + fitness_reason
    │
    ▼ filter_constraints
filtered (List[dict])         # 반경·예산 조건 통과한 후보
    │
    ▼ rank
ranked (List[dict])           # TOP 3
    │
    ▼ compose_response
timeline (Timeline)           # 구조화 일정 객체
response (str)                # 렌더링된 텍스트
```

---

## 6. 외부 API 및 도구

| 도구 | 용도 | 키 | 폴백 |
|------|------|----|------|
| **Upstage Solar Pro** (`solar-pro`) | 의도 파싱 / 후보 선별+점수 / 타임라인 생성 | `UPSTAGE_API_KEY` | 규칙 기반 |
| **Upstage Embeddings** (`solar-embedding-1-large`) | 쿼리·관광지 유사도 검색 | `UPSTAGE_API_KEY` | 전체 목록 반환 |
| **OpenWeather** (5-day forecast) | 여행지 날씨 컨텍스트 주입 | `OPENWEATHER_API_KEY` | 날씨 없이 진행 |
| **Kakao Local API** (FD6·CE7) | 음식점·카페 실제 지점 검색 | `KAKAO_API_KEY` | 빈 리스트 (LLM이 목록 없이 생성) |
| **Nominatim** (OpenStreetMap) | 출발지 지오코딩 | 불필요 | REGION_COORDS → CITY_TO_REGION |
| **LangSmith** | 워크플로우 추적·관측 | `LANGSMITH_API_KEY` | 추적 없이 진행 |

---

## 7. 정적 데이터 (`src/core/`)

### `mock_data.py` — 국내 관광지 50선

각 관광지 딕셔너리 구조:

```python
{
    "name": "경포해변",
    "region": "강원",          # 광역 지역 (REGION_COORDS 키와 일치)
    "type": "자연",
    "mood": ["바다", "활기찬", "개방적"],
    "best_for": ["friends", "couple"],
    "cost_level": "low",       # low | mid | high
}
```

> `import` 시점에 `assert len(TOURIST_SPOTS) == 50` 자체 검증 실행

### `region_coords.py` — 좌표 테이블

```python
REGION_COORDS: dict[str, tuple[float, float]]
# 17개 광역 지역 중심 좌표 (위도, 경도)
# 예: "서울": (37.5665, 126.9780)

CITY_TO_REGION: dict[str, str]
# 구/동 단위 → 광역 지역 매핑 (Nominatim 실패 시 폴백)
# 예: "구로" → "서울", "해운대" → "부산"
```

---

## 8. Pydantic 스키마 (`src/core/schemas.py`)

```
TravelIntent          ← parse_intent 출력 / 전 노드에서 참조
  ├─ intent_type: str
  ├─ location_preference: str | None
  ├─ origin: str | None
  ├─ origins: List[str]
  ├─ travel_radius: str | None
  ├─ transport_mode: str | None
  ├─ duration_nights: int | None
  ├─ start_date: str | None
  ├─ human_count: int
  ├─ participant_type: str
  ├─ constraints: List[str]
  ├─ mood_keywords: List[str]
  └─ budget_level: str | None

FitnessReport         ← generate_and_score 출력
  └─ evaluations: List[SpotFitness]
       ├─ name: str
       ├─ score: int (0~10)
       └─ reason: str

Timeline              ← compose_response 출력
  ├─ destination: str
  └─ items: List[TimelineItem]
       ├─ time: str
       ├─ place: str
       ├─ activity: str
       ├─ transport: str | None
       └─ cost: str | None

SpotSelection         ← (미사용, 통합 전 레거시)
  └─ names: List[str]
```

---

## 9. 프롬프트 구조 (`src/prompts/templates.py`)

| 빌더 함수 | 사용 노드 | 출력 스키마 |
|-----------|----------|-------------|
| `build_intent_messages()` | `parse_intent` | `TravelIntent` |
| `build_clarification_messages()` | `check_sufficiency` | 평문 질문 1개 |
| `build_generate_and_score_messages()` | `generate_and_score` | `FitnessReport` |
| `build_timeline_messages()` | `compose_response` | `Timeline` |

**Few-shot 예시 포함 노드:** `parse_intent` (3개 예시 — 커플/친구/거절)

**핵심 프롬프트 지침:**
- `generate_and_score`: 제공된 후보 목록 외 관광지 생성 금지, 5~8개 선별
- `compose_response`: 제공된 맛집 목록 외 이름 생성 금지, 목록 없으면 `"현지 식당 (목록 참고)"` 표기

---

## 10. Streamlit UI 흐름 (`app/main.py`)

### 화면 흐름

```
① 쿼리 입력 + "✈️ 추천 받기" 클릭
        ↓
② st.status 열림 → app.stream(stream_mode="updates")
   ✅ 의도 파싱
   ✅ 정보 충분성 확인
   ✅ 참여자 분석
   ✅ 후보 선별 + 적합도 평가
   ✅ 제약 필터링
   ✅ 최종 순위 선정
        ↓
③-A needs_clarification == True
   → LINE 채팅 버블로 역질문 표시 (🤖 아바타 + 말풍선)
   → 답변 입력창 + "💬 답변하기" 버튼
   → 원본쿼리 + 답변 합쳐 재실행 (allow_clarification=False)
        ↓
③-B needs_clarification == False
   → 추천 여행지 TOP 3 카드 표시
     (순위 배지 / 이름 / 지역·타입 / 무드 태그 / 적합 이유 / 선택 버튼)
        ↓
④ 카드 선택 ("이 여행지로 보기")
   → selected_spot 저장
   → compose_response 직접 호출 (그래프 재실행 없음)
   → Kakao 맛집+카페 검색 → 타임라인 생성
        ↓
⑤ 타임라인 표시
   → 시간(초록) | 장소(굵게) | 활동 | 이동수단·비용(캡션)
   → "← 다른 여행지 보기" 버튼으로 카드 화면 복귀
```

### session_state 키

| 키 | 타입 | 역할 |
|----|------|------|
| `original_query` | `str` | 원본 쿼리 (역질문 합산용) |
| `ranked` | `List[dict]` | TOP 3 여행지 |
| `intent` | `TravelIntent \| None` | 파싱된 의도 |
| `needs_clarification` | `bool` | 역질문 필요 여부 |
| `clarification_question` | `str` | LLM 생성 역질문 |
| `selected_spot` | `dict \| None` | 사용자 선택 여행지 |
| `timeline_response` | `str` | 렌더링된 타임라인 텍스트 |
| `timeline_object` | `Timeline \| None` | Timeline Pydantic 객체 |
| `workflow_done` | `bool` | 그래프 완료 여부 |
| `run_error` | `str` | 워크플로우 오류 메시지 |

---

## 11. 성능 최적화

| 최적화 | 방법 | 효과 |
|--------|------|------|
| LLM 호출 수 절감 | `generate_candidates` + `evaluate_fitness` → `generate_and_score` 통합 | ~3-5초 절감 |
| 날씨 API 병렬화 | `ThreadPoolExecutor(max_workers=10)` | 순차 N회 → 동시 1회 |
| 임베딩 캐시 | 관광지 passage 임베딩 모듈 레벨 캐시 (`_spot_embeddings_cache`) | 최초 1회만 계산 |
| LLM 인스턴스 캐시 | `_llm_cache` (temperature 별) | `ChatUpstage` 중복 생성 방지 |
| 타임라인 분리 실행 | 카드 선택 후 `compose_response` 직접 호출 | 메인 그래프 대기 없이 카드 즉시 표시 |

---

## 12. 환경변수

```bash
UPSTAGE_API_KEY=        # 필수 — Solar Pro + Embedding
KAKAO_API_KEY=          # 맛집 검색용 (카카오 로컬 서비스 활성화 필요)
OPENWEATHER_API_KEY=    # 날씨 컨텍스트용 (없으면 날씨 없이 진행)
LANGSMITH_API_KEY=      # 선택 — 워크플로우 추적
LANGSMITH_PROJECT=      # 기본값: travel-agentic-workflow
LANGSMITH_TRACING_V2=   # true | false
```

---

## 13. 실행 방법

```bash
# 환경 설정
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env   # API 키 입력

# Streamlit 데모
streamlit run app/main.py

# CLI 단독 실행
python src/agents/structure_a.py

# 평가 쿼리 20선
python tests/test_queries.py
```

# TODO 구현 설계: 외부 API 연동 (Approach A)

**날짜:** 2026-06-07  
**대상 브랜치:** feature/sungyoon  
**관련 파일:** `src/agents/structure_a.py`, `src/core/schemas.py`, `src/core/mock_data.py`, `src/prompts/templates.py`, `src/config.py`

---

## 1. 목표

`structure_a.py`의 4개 TODO 노드를 외부 API(Kakao REST, OpenWeather, Upstage 임베딩)와 연동해 실제 동작하도록 구현한다. 각 노드는 API 실패 시 기존 규칙 기반 폴백으로 자동 복귀해 그래프 안정성을 유지한다.

---

## 2. 새 파일 구조

```
src/
  tools/
    __init__.py
    kakao_map.py      # Kakao 키워드 검색(지오코딩) + 하버사인 거리 계산
    weather.py        # OpenWeather 5일 예보 파싱
    embeddings.py     # Upstage 임베딩 + 코사인 유사도 검색
  core/
    schemas.py        # TravelIntent.origins: List[str] 추가
    mock_data.py      # 각 spot에 cost_level 필드 추가
  config.py           # KAKAO_API_KEY, OPENWEATHER_API_KEY 로드
  agents/
    structure_a.py    # 4개 노드 구현 교체
  prompts/
    templates.py      # origins 추출 프롬프트 규칙 추가
.env.template         # KAKAO_API_KEY, OPENWEATHER_API_KEY 항목 추가
requirements.txt      # requests 추가
```

---

## 3. 환경 변수

| 변수 | 설명 |
|------|------|
| `KAKAO_API_KEY` | Kakao REST API 키 (JavaScript 키가 아닌 REST API 키) |
| `OPENWEATHER_API_KEY` | OpenWeather API 키 (무료 플랜 가능) |
| `UPSTAGE_API_KEY` | 기존 — 임베딩에도 재사용 |

---

## 4. 노드별 설계

### 4-1. `classify_mode` — multi_origin 분기

**스키마 변경 (`schemas.py`)**
```python
origins: List[str] = Field(
    default_factory=list,
    description="복수 출발지 목록. 참여자들이 서로 다른 곳에서 출발할 때 각 출발지를 기입."
)
```

**프롬프트 규칙 추가 (`templates.py`)**
- `origins`: 참여자들이 서로 다른 출발지에서 모인다고 명시되면 각 출발지를 리스트로 추출. 출발지가 하나이거나 불명확하면 빈 리스트.

**분기 로직 (`structure_a.py`)**
```
len(intent.origins) > 1  →  multi_origin
intent.human_count > 1   →  group_single_origin
else                      →  single
```

multi_origin 모드는 현재 파이프라인에서 state에 기록만 하고 동일 흐름으로 진행 (미래 다중 출발지 최적화 확장점).

---

### 4-2. `generate_candidates` — Upstage 임베딩 RAG

**툴 (`src/tools/embeddings.py`)**
- `embed_texts(texts: List[str]) -> List[List[float]]`: Upstage 임베딩 API 배치 호출
  - passage 모델: `solar-embedding-1-large-passage` (스팟 인덱싱)
  - query 모델: `solar-embedding-1-large-query` (사용자 쿼리)
- `cosine_similarity(a, b) -> float`: 넘파이 없이 순수 Python math로 계산
- `_spot_embeddings_cache`: 모듈 수준 dict — 첫 호출 시 50개 스팟 일괄 임베딩 후 캐시

**스팟 임베딩 텍스트 포맷**
```
{name} {region} {type} {" ".join(mood)} {" ".join(best_for)}
```

**generate_candidates 노드 흐름**
1. 캐시된 스팟 임베딩 로드 (없으면 일괄 생성)
2. `user_query` 임베딩 (query 모델)
3. 코사인 유사도 내림차순 정렬 → 상위 15개 추출
4. 기존 LLM 정제(`SpotSelection`) 단계 통과 → 최종 후보
5. 폴백: 임베딩 API 실패 시 기존 지역 규칙 필터

---

### 4-3. `evaluate_fitness` — OpenWeather 날씨 컨텍스트

**툴 (`src/tools/weather.py`)**
- `get_weather(lat, lon, target_date) -> dict`: OpenWeather 5일/3시간 예보 API
  - `target_date`(YYYY-MM-DD) 기준 낮 시간대 예보 1개 선택
  - `target_date` 없거나 5일 이후면 첫 번째 예보 사용
  - 반환: `{"description": str, "temp": float, "rain_prob": float}`
- `REGION_COORDS`: 서울·부산·강원·제주 등 광역 지역 중심 좌표 정적 딕셔너리

**evaluate_fitness 노드 흐름**
1. 각 후보 스팟의 `region` → `REGION_COORDS` → OpenWeather 호출
2. 날씨 정보를 LLM 평가 메시지에 추가 컨텍스트로 주입
   ```
   [날씨 정보]
   - 해운대해수욕장(부산): 맑음, 24°C, 강수확률 5%
   - 설악산(강원): 흐림, 18°C, 강수확률 40%
   ```
3. 기존 LLM 점수 평가 진행 (날씨 반영해 점수 향상)
4. 폴백: API 실패 시 날씨 컨텍스트 없이 기존 LLM 평가

---

### 4-4. `filter_constraints` — Kakao 거리 필터 + 예산 필터

**툴 (`src/tools/kakao_map.py`)**
- `geocode(query: str) -> tuple[float, float]`: Kakao 키워드 검색 API → `(lat, lon)`
- `haversine(lat1, lon1, lat2, lon2) -> float`: 직선 거리(km) 계산 (순수 Python)
- `REGION_COORDS`: `weather.py`와 공유하는 정적 지역 좌표 딕셔너리 → `src/tools/region_coords.py`로 분리

**travel_radius 파싱 규칙**
| 값 | 거리 상한 |
|----|-----------|
| `근교` | 150km |
| `당일치기` | 100km |
| `전국` | 무제한 |
| `"100km 이내"` 등 숫자 포함 | 파싱한 km |
| `None` | 무제한 |

**mock_data `cost_level` 필드 추가**
- `low`: 자연, 역사(무료/소액 입장료)
- `mid`: 식도락, 도시, 체험(일반)
- `high`: 체험(테마파크·리조트)

**budget_level 필터**
| budget_level | 허용 cost_level |
|--------------|-----------------|
| `low` | low만 |
| `mid` | low, mid |
| `high` | 전부 통과 |
| `None` | 전부 통과 |

**filter_constraints 노드 흐름**
1. `origin` 있으면 Kakao 지오코딩 → 좌표
2. 각 스팟 region → `REGION_COORDS` → 하버사인 거리
3. `travel_radius` 파싱 → 거리 초과 스팟 제거
4. `budget_level` 규칙 → `cost_level` 불일치 스팟 제거
5. 필터 후 후보가 0개면 필터 무시(전체 통과)
6. 폴백: Kakao API 실패 시 budget 필터만 적용

---

## 5. 공유 상수 (`src/tools/region_coords.py`)

`weather.py`와 `kakao_map.py` 모두 사용하는 광역 지역 좌표를 별도 모듈로 분리해 중복 제거.

```python
REGION_COORDS: dict[str, tuple[float, float]] = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "강원": (37.8228, 128.1555),
    "제주": (33.4996, 126.5312),
    "경북": (36.4919, 128.8889),
    "전북": (35.8242, 127.1480),
    "전남": (34.8161, 126.4630),
    "충남": (36.5184, 126.8000),
    "충북": (36.6357, 127.4914),
    "경남": (35.4606, 128.2132),
    "대구": (35.8714, 128.6014),
    "대전": (36.3504, 127.3845),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
}
```

---

## 6. 에러 처리 원칙

- 각 툴 함수는 실패 시 `None` 또는 빈 값 반환 (예외 전파 금지)
- 노드 내 `try/except`로 툴 실패를 감지해 폴백 분기
- 기존 폴백 로직(`except Exception:` 블록)은 그대로 유지

---

## 7. 의존성 추가

```
requests          # Kakao, OpenWeather HTTP 호출
```

Upstage 임베딩은 `langchain-upstage`의 `UpstageEmbeddings` 클래스 사용 (이미 설치됨).

---

## 8. 변경 파일 요약

| 파일 | 변경 유형 |
|------|-----------|
| `src/core/schemas.py` | `origins` 필드 추가 |
| `src/core/mock_data.py` | `cost_level` 필드 추가 (50개) |
| `src/config.py` | `KAKAO_API_KEY`, `OPENWEATHER_API_KEY` 로드 |
| `src/prompts/templates.py` | `origins` 추출 규칙 + 날씨 컨텍스트 빌더 추가 |
| `src/agents/structure_a.py` | 4개 노드 구현 교체 |
| `src/tools/__init__.py` | 신규 |
| `src/tools/region_coords.py` | 신규 |
| `src/tools/kakao_map.py` | 신규 |
| `src/tools/weather.py` | 신규 |
| `src/tools/embeddings.py` | 신규 |
| `.env.template` | 신규 키 항목 |
| `requirements.txt` | `requests` 추가 |

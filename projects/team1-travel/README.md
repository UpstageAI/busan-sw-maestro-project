# asm-team1-ai-study

# 🧭 자연어 기반 여행지 추천 에이전트

> Upstage Agentic Workflow 실습 프로젝트 — **관측성(Observability) · 구조화(Structuring) · 흐름 제어(Flow Control)** 를 핵심 가치로 삼아 자연어 여행 요청을 구조화된 의도로 변환하고 국내 여행지를 추천하는 에이전트.

---

## 1. 서비스 정의

사용자가 자유로운 자연어로 입력한 여행 요청(예: *"여자친구랑 2박 3일 조용한 바다 여행 가고 싶어"*)을
구조화된 의도(`TravelIntent`)로 변환하고, 규칙 기반 국내 관광지 데이터에서 적합한 여행지를 추천합니다.

## 2. 범위 고정 (Singleton Scope)

본 프로젝트는 **싱글턴(단일 턴) 추천**으로 범위를 고정합니다.
즉, 대화 맥락을 누적하는 멀티턴 챗봇이 아니라, **하나의 요청 → 하나의 추천 응답**을 정확하고 빠르게 처리하는 데 집중합니다.

## 3. 아키텍처 — 구조 A (baseline)

LangGraph 기반 **4단계 정석 워크플로우**로 구현합니다. (구조 B 는 본 단계 범위 밖)

```
parse_intent  →  retrieve_spots  →  rank_and_select  →  compose_response
(의도 구조화)     (후보 검색)        (정렬/선별)          (추천 응답 생성)
```

| 단계 | 노드 | 역할 |
|------|------|------|
| 1 | `parse_intent` | 자연어 → `TravelIntent` 구조화 (Solar Pro) |
| 2 | `retrieve_spots` | Mock 관광지 50선에서 규칙 기반 후보 검색 |
| 3 | `rank_and_select` | 의도에 맞춰 후보 정렬·선별 |
| 4 | `compose_response` | 최종 추천 응답 생성 |

## 4. 실습 스택

| 영역 | 기술 |
|------|------|
| LLM | **Upstage Solar Pro** (`langchain-upstage`) |
| 워크플로우 | **LangGraph** |
| 관측성/추적 | **LangSmith** |
| 데이터 검증 | **Pydantic v2** |
| 데모 UI | **Streamlit** |
| 환경 변수 | **python-dotenv** |

## 5. 디렉토리 구조

```
.
├── app/
│   └── main.py            # Streamlit 로컬 데모 UI
├── src/
│   ├── config.py          # 환경변수 로드 및 LangSmith 세팅 연결
│   ├── agents/
│   │   └── structure_a.py # 4단계 정석 워크플로우 (구조 A)
│   ├── core/
│   │   ├── schemas.py     # 구조화 데이터 스키마 (TravelIntent)
│   │   └── mock_data.py   # 규칙 기반 국내 관광지 50선
│   └── prompts/
│       └── templates.py   # 시스템 프롬프트 및 Few-shot
└── tests/
    └── test_queries.py    # 지연시간/정확도 평가용 쿼리 20선
```

## 6. 로컬 실행 방법

> ⚠️ **Python 3.10 필수.** `langchain-upstage` 가 의존하는 `tokenizers` 는
> Python 3.14 등 최신 버전에서 미리 빌드된 wheel 이 없어 설치가 실패합니다.
> 반드시 **Python 3.10** 으로 가상환경을 생성하세요.

```bash
# 1) 가상환경 생성 및 활성화 (Python 3.10 사용)
py -3.10 -m venv venv          # Windows (py launcher)
venv\Scripts\activate          # Windows
# python3.10 -m venv venv      # Mac/Linux
# source venv/bin/activate     # Mac/Linux

# 2) 의존성 설치
pip install -r requirements.txt

# 3) 환경 변수 설정 (.env.template 복사 후 실제 키 입력)
copy .env.template .env        # Windows
# cp .env.template .env        # Mac/Linux

# 4) 데모 실행
streamlit run app/main.py
```

## 7. 환경 변수

`.env.template` 을 복사해 `.env` 를 만들고 실제 키를 입력하세요. (`.env` 는 Git 추적 제외)

| 변수 | 설명 |
|------|------|
| `UPSTAGE_API_KEY` | Upstage Solar API Key |
| `LANGSMITH_API_KEY` | LangSmith 관측성 API Key |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트명 (`travel-agentic-workflow`) |

## 8. 개발 로드맵

- [x] 초기 환경 세팅 (venv, requirements, .env.template, .gitignore)
- [x] 디렉토리 스캐폴딩 (구조 A)
- [x] `TravelIntent` Pydantic v2 스키마 선제 구현
- [x] Mock 관광지 50선 데이터
- [ ] `parse_intent` Solar Pro 연동 (의도 추출)
- [ ] `compose_response` Solar Pro 연동 (추천문 생성)
- [ ] LangSmith 추적 검증
- [ ] 평가 쿼리 20선 기반 정확도/지연시간 측정

---

**작성자:** 문인호 · ASM Team 1

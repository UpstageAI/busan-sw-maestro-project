# 마인크래프트 초보 가이드 챗봇 (Minecraft Guide Agent)

마인크래프트 초보자의 현재 상황(자원·진척도)을 파악해 목표까지의 **"다음 한 걸음"** 을 단계별로 안내하는 LLM 에이전트.

**스택**: FastAPI · LangGraph · MySQL · Qdrant · Upstage Solar · (검증용) Streamlit

> 이 디렉토리(`project_code/`)가 백엔드와 검증용 웹뷰의 루트입니다.
> 실제 메인 클라이언트는 **Fabric 모드**이고, 웹뷰(Streamlit)는 챗봇 동작 검증용입니다. 둘 다 동일한 FastAPI API를 호출합니다.

---

## 빠른 시작 (팀원 온보딩)

사전 준비: [uv](https://docs.astral.sh/uv/) · Docker · `UPSTAGE_API_KEY` · (공유 벡터 사용 시) Qdrant Cloud `QDRANT_URL`/`QDRANT_API_KEY`

```bash
# 1) 환경변수
cp .env.example .env            # UPSTAGE_API_KEY 등 입력

# 2) 로컬 DB 기동 (MySQL + Qdrant)
docker compose up -d mysql qdrant

# 3) 의존성 설치 (Python 3.12 고정 — .python-version)
uv sync

# 4) DB 스키마 적용 (Alembic)
uv run alembic upgrade head

# 5) (데이터 수집자만) 위키 → Qdrant 적재
uv run python scripts/ingest_wiki.py --limit 50   # 시범(속도 보정)
uv run python scripts/ingest_wiki.py              # 전체 적재

# 6) 백엔드 + 웹뷰 실행
bash start.sh
#   Backend  → http://localhost:8001   (POST /api/v1/chat/sync)
#   Frontend → http://localhost:8002   (Streamlit)
```

---

## 협업 모델 (이 DB를 팀이 어떻게 쓰나)

- **MySQL**: 각자 로컬(docker-compose). 세션/메시지는 일회성 개발 데이터라 공유하지 않는다.
- **Qdrant 위키 벡터**: 공유 Qdrant Cloud에 **1회 적재** → 팀원은 `QDRANT_URL`/`QDRANT_API_KEY`로 연결만 (재임베딩 불필요).
- **스키마 변경**: `app/models.py` 수정 → `uv run alembic revision --autogenerate -m "변경 내용"` → 커밋. 팀원은 `uv run alembic upgrade head`로 동기화.
- **데이터 접근**: DB 내부를 몰라도 아래 함수만 호출하면 된다.
  - `app/repositories.py` — `get_or_create_session`, `append_message`, `get_recent_messages`, `get/upsert_coaching_state`
  - `app/vector_store.py` — `search_documents(query, n_results)`

---

## 구조

```
app/
  main.py            FastAPI 앱 (/health)
  api.py             /chat(SSE), /chat/sync (+ 세션·메시지·진척도 저장, 인벤토리·게임상태 수신)
  graph.py           LangGraph 11노드 (아래 워크플로우 참고)
  agents/            노드 구현
    query_analyzer.py    도메인/키워드/intent 분석
    goal_resolver.py     목표 클래스 분류 + 막연형 목표 제안 (LLM)
    clarifier.py         되묻기 판단
    retrieval.py         Qdrant 위키 + 확정 사실 조회
    web_searcher.py      RAG 부족 시 웹검색 폴백
    material_checker.py  제작 목표 부족 재료·티어 결정론 계산 + 레시피 격자
    session_memory.py    load_state / reconcile / persist_state (멀티턴 진척도)
    responder.py         코칭 응답 생성(minecraft는 토큰 스트리밍)
  knowledge/         결정론 지식 — RAG 환각 방지용
    recipes.json         게임 jar에서 추출한 레시피(읽기 전용)
    recipes.py           레시피 로더 + recipe_grid(3×3 정규화)
    planner.py           plan_materials(부족 재료·티어) · next_action(다음 단계)
    goal_resolver.py     한국어 질문 → 제작 목표 item id
    facts.py             질문/인벤토리 → 확정 규칙 조회
    minecraft_facts.py   티어·레시피·아이템 ID↔한국어명 테이블
  web_search.py      wiki_search(키 없는 마크 위키) · tavily_search(선택)
  prompts/templates.py   노드별 시스템 프롬프트 + 프롬프트 블록 포맷터
  core/
    config.py        환경설정 (LLM·Qdrant·웹검색)
    database.py      MySQL (SQLAlchemy engine/Session/Base)
    vector_db.py     Qdrant 클라이언트 (cloud/local)
    embedding.py     Upstage 임베딩 (동적 차원)
    llm.py           Upstage Solar
  models.py          User / ChatSession / Message / CoachingState
  repositories.py    DB 데이터 접근 계층 (팀 공용 인터페이스)
  vector_store.py    Qdrant 검색
  schemas.py         AgentState · 요청/응답 스키마
alembic/             DB 마이그레이션 (0001_initial, 0002_coaching_state)
scripts/             ingest_wiki.py(위키→Qdrant) · extract_recipes.py(jar→recipes.json)
frontend/ui.py       Streamlit 검증용 웹뷰
```

### LangGraph 워크플로우 (11노드)

```
START → load_state → analyze ─(domain)─┬─ general·out_of_scope ───────────────────→ respond ─┐
                                        └─ minecraft → resolve_goal → clarify ─(충분?)─┬ 부족→ask┤
                                            retrieve → web_search → check_materials ←─ 충분       │
                                              → reconcile → respond ──────────────────────────────┤
                                                                                    persist_state → END
```

- **load_state / reconcile / persist_state** (`session_memory`) — `coaching_state`로 턴 간 진척도 로드·진행 인식·저장
- **analyze** (`query_analyzer`) — domain·keywords·intent 추출
- **resolve_goal** (`goal_resolver`) — 목표 클래스(craft/survival/explore/vague) 분류 + 막연하면 다음 목표 제안
- **clarify** (`clarifier`) — 정보 부족 시 되묻기. 인벤토리 연동이거나 직전 턴이 되묻기면 스킵
- **retrieve** (`retrieval`) — Qdrant 위키 검색 + 확정 사실 조회
- **web_search** (`web_searcher`) — RAG 커버리지 부족 시에만 마크 위키(키 없음)로 보강
- **check_materials** (`material_checker`) — 제작 목표면 부족 재료·티어 결정론 계산 + 3×3 격자 첨부
- **respond** (`responder`) — 상태·진행을 종합한 코칭 응답(minecraft는 토큰 스트리밍)

---

## API 계약 (웹뷰·Fabric 모드 공용)

| 엔드포인트 | 설명 |
| --- | --- |
| `POST /api/v1/chat/sync` | 동기 응답 `{ answer, domain, sources, todos, recipe }` — `/coach` 채팅 명령이 사용 |
| `POST /api/v1/chat` | SSE 스트리밍 (노드 진행 + 토큰 + `done`) — **코치 창**과 웹뷰가 사용 |
| `GET /api/v1/sessions` · `/sessions/{thread_id}/messages` · `DELETE /sessions/{thread_id}` | 대화 목록·메시지·삭제 (웹뷰) |
| `GET /health` | 상태 확인 |

- 요청 본문: `{ message, thread_id, inventory[], inventory_connected, game_state }` — `thread_id`로 세션·진척도 식별·저장
- `inventory`·`game_state`는 **모드만** 채운다(인게임 보유 아이템·시간·체력·좌표). 웹뷰는 비운다.
- `recipe`는 제작 목표가 있을 때만 채워지는 3×3 격자(`{ output, count, grid[9] }`).

## 진행 현황

**완료**: DB 인프라(MySQL+Qdrant) · Alembic 스키마 · 위키 RAG + 키 없는 웹검색 폴백 · **11노드 Agentic 워크플로우**(목표 해석 · 결정론 제작 엔진 · 멀티턴 진척도 · 게임 상태 인식 · 가드레일) · 3×3 레시피 격자 · 세션/메시지/진척도 저장 · 검증용 웹뷰

**남은 작업**: 웹뷰 ASCII 레시피 폴백 · 세션 장기 요약 · 배포

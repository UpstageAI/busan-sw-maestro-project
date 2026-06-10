# PRD: 소마 에이전트 — 오케스트레이션 / 세션·컨텍스트 관리

> 담당 영역: 오케스트레이션 (LangGraph), 세션 관리, 컨텍스트 관리  
> 연관 담당자: 김응현·김진·노기현·배재현·박태원  
> 최종 수정: 2026-06-04

---

## 1. 목적 및 범위

### 1.1 목적

LangGraph + FastAPI를 이용하여 소마 에이전트의 **런타임 워크플로우**를 구현한다.  
구체적으로는 다음 세 가지를 책임진다.

| 영역 | 설명 |
|------|------|
| **오케스트레이션** | 사용자 질문을 의도에 따라 올바른 노드(핸들러)로 라우팅하는 LangGraph 그래프 |
| **세션 관리** | 사용자별 독립 대화 세션 생성·유지·만료 |
| **컨텍스트 관리** | 한 턴 내 상태(`AgentState`) 및 다중 턴 대화 히스토리 관리 |

### 1.2 범위 외

- 문서 수집·파싱·임베딩 (Data Ingestion Pipeline) — 별도 담당
- ChromaDB 검색 로직 세부 구현 — 별도 담당
- LLM 프롬프트 세부 튜닝 — 협업으로 결정
- Streamlit 프론트엔드 — 별도 담당

---

## 2. 시스템 상태 (AgentState)

다이어그램의 **SYSTEM STATE** 박스에 명시된 5개 필드를 TypedDict로 정의한다.

```python
class AgentState(TypedDict):
    # 원본 사용자 질문
    question: str

    # 의도 분류 결과
    # "general" | "soma_unrelated" | "soma_query" | "soma_summarize" | "schedule_link"
    intent: str

    # 벡터 DB에서 검색된 상위 청크 목록 (최대 5개)
    retrieved_chunks: list[dict]  # {"content": str, "source": str, "score": float}

    # LLM이 생성한 최종 답변 문자열
    generated_answer: str

    # 현재 턴의 노드 실행 순서 기록 (디버깅·로깅용)
    execution_history: list[str]

    # 다중 턴: 직전 N개 대화 (세션에서 주입)
    chat_history: list[dict]  # {"role": "user"|"assistant", "content": str}
```

---

## 3. LangGraph 워크플로우 설계

### 3.1 노드 목록

| 노드 ID | 역할 |
|---------|------|
| `router` | 질문을 분석해 `intent` 필드 결정 |
| `handle_general` | 일반 대화·잡담 응답 생성 |
| `handle_irrelevant` | 소마 무관 질문 거절 메시지 반환 |
| `retrieve_documents` | ChromaDB 벡터 검색 수행 |
| `check_documents_found` | 검색 결과 유무 판단 (조건 분기) |
| `handle_not_found` | 결과 없을 시 공식 계정 안내 |
| `process_by_intent` | 의도별 처리 분기 (query / summarize / extract) |
| `generate_answer` | RAG 답변 생성 (출처 포함) |
| `generate_summary` | 다중 문서 요약 생성 |
| `format_schedule_link` | 일정·링크 구조화 추출 |

### 3.2 엣지 (라우팅 로직)

```
START
  └─► router
        ├─[general]         ─► handle_general        ─► END
        ├─[soma_unrelated]  ─► handle_irrelevant      ─► END
        └─[검색 필요 3종]   ─► retrieve_documents
                                  └─► check_documents_found
                                        ├─[found=False]  ─► handle_not_found  ─► END
                                        └─[found=True]   ─► process_by_intent
                                                               ├─[query]    ─► generate_answer      ─► END
                                                               ├─[summarize]─► generate_summary     ─► END
                                                               └─[extract]  ─► format_schedule_link ─► END
```

### 3.3 조건부 엣지 구현 포인트

```python
def route_after_intent(state: AgentState) -> str:
    intent = state["intent"]
    if intent == "general":
        return "handle_general"
    if intent == "soma_unrelated":
        return "handle_irrelevant"
    return "retrieve_documents"  # soma_query / soma_summarize / schedule_link

def route_after_retrieve(state: AgentState) -> str:
    return "process_by_intent" if state["retrieved_chunks"] else "handle_not_found"

def route_by_intent(state: AgentState) -> str:
    mapping = {
        "soma_query":     "generate_answer",
        "soma_summarize": "generate_summary",
        "schedule_link":  "format_schedule_link",
    }
    return mapping[state["intent"]]
```

---

## 4. 세션 관리

### 4.1 세션 모델

```python
class Session:
    session_id: str          # UUID4
    created_at: datetime
    last_active: datetime
    chat_history: list[dict] # 최근 N턴 대화 (기본 10턴)
    metadata: dict           # 필요 시 확장 (user_id 등)
```

### 4.2 세션 저장소 (MVP)

- **인메모리 딕셔너리** (`dict[str, Session]`)
- TTL: 마지막 활성 시각 기준 **30분** 경과 시 자동 만료
- 만료 정리: FastAPI `startup` 이벤트에서 백그라운드 태스크 등록 (60초 주기)

> MVP 이후 확장: Redis를 저장소로 교체해 수평 확장 지원

### 4.3 세션 생명주기

```
POST /sessions          → 새 session_id 발급
POST /chat/{session_id} → 대화 요청 (세션 히스토리 로드 → 그래프 실행 → 히스토리 갱신)
DELETE /sessions/{id}   → 명시적 세션 종료 (선택)
```

---

## 5. 컨텍스트 관리

### 5.1 다중 턴 히스토리 주입

매 요청마다 `AgentState.chat_history`에 최근 **10턴**만 슬라이싱해 주입한다.  
LLM 호출 시 시스템 프롬프트 + 히스토리 + 현재 질문 + 검색 청크 순서로 조립한다.

```python
def build_context_messages(state: AgentState) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(state["chat_history"][-10:])  # 최근 10턴
    # 검색 청크는 user 메시지 내 컨텍스트 블록으로 삽입
    messages.append({"role": "user", "content": format_user_message(state)})
    return messages
```

### 5.2 컨텍스트 길이 제어

| 항목 | 기본값 | 비고 |
|------|--------|------|
| 히스토리 최대 턴 수 | 10턴 | 설정값으로 추출 예정 |
| 검색 청크 최대 개수 | 5개 | 기획서 명시 |
| 청크 당 최대 토큰 | 500 tokens | 초과 시 truncate |

### 5.3 상태 초기화 (`reset_turn_state`)

새 턴마다 이전 턴의 `retrieved_chunks`, `generated_answer`, `execution_history`를 초기화하고 `chat_history`만 세션에서 인계한다.

---

## 6. FastAPI 엔드포인트 설계

### 6.1 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/sessions` | 새 세션 생성, `session_id` 반환 |
| `POST` | `/chat/{session_id}` | 메시지 전송 및 응답 수신 |
| `GET`  | `/sessions/{session_id}` | 세션 히스토리 조회 |
| `DELETE` | `/sessions/{session_id}` | 세션 삭제 |
| `GET`  | `/health` | 헬스체크 |

### 6.2 요청/응답 스키마

```python
# POST /chat/{session_id}
class ChatRequest(BaseModel):
    message: str

class SourceDocument(BaseModel):
    source: str
    content: str   # 청크 미리보기 (100자)

class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: list[SourceDocument]
    session_id: str
    execution_history: list[str]  # 개발 중 디버깅용, 프로덕션에서 제거 가능
```

### 6.3 처리 흐름

```
POST /chat/{session_id}
  1. 세션 존재 확인 (없으면 404)
  2. 세션에서 chat_history 로드
  3. AgentState 초기화 (question + chat_history 주입)
  4. LangGraph 그래프 실행 (graph.invoke(state))
  5. chat_history에 이번 턴 (user/assistant) append
  6. 세션 last_active 갱신
  7. ChatResponse 반환
```

---

## 7. 오류 처리

| 시나리오 | 처리 방식 |
|----------|-----------|
| 세션 없음 | HTTP 404 |
| 만료된 세션 | HTTP 410 Gone |
| LLM API 타임아웃 | HTTP 504, 재시도 없음 (MVP) |
| ChromaDB 연결 실패 | `handle_not_found` 노드로 폴백 |
| 의도 분류 실패 (모델 오류) | `general` 로 기본값 처리 |

---

## 8. 비기능 요구사항 (MVP 기준)

| 항목 | 목표 |
|------|------|
| 응답 지연 | P90 < 5초 (로컬 환경) |
| 동시 세션 | 최소 10개 (로컬 단일 프로세스) |
| 세션 히스토리 보존 | 30분 TTL |
| 그래프 재사용 | 애플리케이션 시작 시 한 번 컴파일, 공유 |

---

## 9. 디렉터리 구조 (제안)

```
sadari/
├── src/
│   ├── agent/
│   │   ├── graph.py          # LangGraph 그래프 정의 (노드·엣지 조립)
│   │   ├── state.py          # AgentState TypedDict
│   │   ├── nodes/
│   │   │   ├── router.py
│   │   │   ├── handle_general.py
│   │   │   ├── handle_irrelevant.py
│   │   │   ├── retrieve.py
│   │   │   ├── generate_answer.py
│   │   │   ├── generate_summary.py
│   │   │   ├── format_schedule.py
│   │   │   └── handle_not_found.py
│   │   └── prompts.py        # 시스템 프롬프트·노드별 프롬프트 상수
│   ├── session/
│   │   ├── manager.py        # SessionManager (생성·조회·만료)
│   │   └── models.py         # Session 데이터 클래스
│   ├── api/
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── routes/
│   │   │   ├── chat.py       # /chat 라우터
│   │   │   └── sessions.py   # /sessions 라우터
│   │   └── schemas.py        # Pydantic 요청·응답 모델
│   └── config.py             # 환경변수·설정값 중앙 관리
├── tests/
│   ├── test_graph.py
│   ├── test_session.py
│   └── test_api.py
├── requirements.txt
└── .env.example
```

---

## 10. 단계별 구현 순서

### Phase 1 — 뼈대 (다른 담당자 병렬 작업 가능)
- [ ] `AgentState` 정의 (`state.py`)
- [ ] LangGraph 그래프 뼈대 (노드는 `pass` 스텁) + 라우팅 로직
- [ ] `SessionManager` 인메모리 구현
- [ ] FastAPI 앱 + `/sessions`, `/chat` 엔드포인트 스텁

### Phase 2 — 노드 연동
- [ ] `router` 노드: LLM 기반 의도 분류 (5종)
- [ ] `retrieve_documents` 노드: ChromaDB 검색 팀과 인터페이스 합의
- [ ] `generate_answer` / `generate_summary` / `format_schedule_link` 노드 구현
- [ ] 컨텍스트 히스토리 주입 로직

### Phase 3 — 통합 및 검증
- [ ] Streamlit 프론트 팀과 API 연동 테스트
- [ ] 4개 시나리오 end-to-end 검증
- [ ] 세션 만료 TTL 검증
- [ ] 오류 케이스 테스트

---

## 11. 인터페이스 합의 필요 사항

| 항목 | 협의 대상 | 내용 |
|------|-----------|------|
| `retrieved_chunks` 스키마 | 검색 담당 | 필드명·형식 통일 |
| LLM 클라이언트 | 전체 | 공용 wrapper 사용 여부 |
| 시스템 프롬프트 | 전체 | 최종 문구 합의 |
| Streamlit ↔ FastAPI | 프론트 담당 | `session_id` 쿠키/로컬스토리지 관리 방식 |

# 소마 에이전트 — Gemini Code Assist 리뷰 가이드

## 언어

모든 리뷰 코멘트는 **한국어**로 작성한다.

## 프로젝트 개요

SW마에스트로 부산 연수생을 위한 RAG 기반 AI 챗봇.
LangGraph로 오케스트레이션하고 FastAPI로 제공하며, Upstage Solar 임베딩 + ChromaDB로 검색한다.

## 핵심 구조

```
src/
├── config.py              # Settings 싱글톤 (lru_cache)
├── agent/
│   ├── state.py           # AgentState TypedDict — 그래프 전체 공유 상태
│   ├── graph.py           # LangGraph StateGraph 조립
│   └── nodes/             # 노드 1개 = 파일 1개 원칙
├── session/               # 인메모리 세션 관리 (TTL 30분)
└── api/                   # FastAPI 라우터
```

## 리뷰 시 중점 확인 항목

### AgentState 관련
- `execution_history` 는 `Annotated[list[str], operator.add]` 누적 필드다. 노드가 `[]` 로 덮어쓰지 않고 `["노드명"]` 을 반환하는지 확인한다.
- `chat_history` 는 세션에서 주입되는 필드다. 노드 내부에서 직접 수정하면 안 된다.

### 노드 구현 원칙
- 각 노드 함수는 `AgentState` 를 받아 `dict` 를 반환해야 한다.
- LLM을 호출하지 않는 노드 (handle_irrelevant, handle_not_found) 는 정적 문자열만 반환한다. LLM 호출 추가를 제안하지 않는다.
- `get_settings()`, `get_client()` 는 모두 싱글톤이다. 노드 내부에서 새로 인스턴스를 생성하지 않는다.

### 라우팅
- 의도 분류는 `INTENT_VALUES` 상수 범위 안에서만 유효하다. 새 의도값 추가 시 `state.py`, `graph.py`, `router.py` 세 곳을 함께 수정해야 한다.
- 조건부 엣지 함수 (`_route_after_router`, `_route_after_retrieve`) 는 반드시 그래프에 등록된 노드 이름 문자열만 반환해야 한다.

### 세션
- `session_manager` 는 전역 싱글톤이다. 테스트나 라우트에서 새로 생성하지 않는다.
- TTL 체크는 `get()` 호출 시 자동으로 수행된다. 별도로 만료 여부를 검사하는 코드를 중복 추가하지 않는다.

### FastAPI
- 세션 없음 → 404, 그 외 서버 오류 → 500. 에러 코드를 임의로 바꾸지 않는다.
- `graph.invoke()` 는 동기 호출이다. async 엔드포인트로 변경 시 `graph.ainvoke()` 로 함께 교체해야 한다.

## 리뷰하지 않아도 되는 항목

- `data/` 디렉터리 하위 파일 (런타임 생성, git 미추적)
- `__pycache__` 관련
- LF/CRLF 줄바꿈 경고 (Windows 환경 특성)
- 프롬프트 문구의 한국어 표현 (기획팀 결정 사항)

## 코드 스타일

- Python 3.11, `from __future__ import annotations` 사용
- 타입 힌트 필수
- 함수 단위 주석은 "WHY가 명확하지 않은 경우"에만 작성
- 불필요한 추상화·헬퍼 추가 제안은 하지 않는다 (MVP 기준)

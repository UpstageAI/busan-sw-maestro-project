# backend AGENTS.md (backend 정본)

FastAPI + LangGraph 기반 Action Router Agent 백엔드. backend 단독 uv 프로젝트.

상위 참조: 전체 구조/문서 맵은 루트 AGENTS.md / README.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

## 구조

- `app/main.py` - FastAPI 인스턴스. `GET /health` + 라우터(`/analyze`, `/run`, `/resume`, `/storage`, `/mock/*` 그리고 6-3 `/confirm`, `/feedback/*`) 등록. lifespan 에서 `init_db()`.
- `app/analysis/` - 6-1 분석 파이프라인(Context stub -> LLM -> 검증/재시도 -> completeness).
- `app/llm/` - Solar/FakeLLM 클라이언트. `UPSTAGE_API_KEY` 없으면 FakeLLM 폴백.
- `app/schemas/` - Pydantic 모델. items(6-1 출력=6-2 입력 공통 정본) / analysis(6-1 내부 raw/Context/AnalyzeResult) / routing(Tool선택,충돌) / approval(승인,실행결과) = 도메인. run(=/run,/resume 전송) = 그래프 레이어.
- `app/storage/` - SQLite(`storage.db`). db(스키마+경로훅) / seed(시연용,명시호출) / queries(조회).
- `app/tools/` - Local Tool 함수 + `TOOL_REGISTRY`.
- `app/conflict/` - 규칙 기반 중복/충돌 검사(LLM 미사용).
- `app/agent/` - 단일 LangGraph. state(AgentState) / nodes(analysis(pass-through), tool_selection, conflict_check, approval(interrupt), execution, feedback_seam(6-3 연결부)) / graph(MemorySaver+interrupt).
- `app/api/routes/` - `analyze`(6-1 분석), `run`(`/run` 시작->interrupt, `/resume` 재개), `confirm`/`feedback`(6-3).
- `app/mock_data/` - 6-2 단독/데모용 6-1 Item 샘플 입력.
- `app/logging_config.py` - `agent.*` 분기/단계 로깅.
- `tests/` - pytest. conftest(tmp DB 격리) + 단위/엔드포인트 테스트.
- 6-3(피드백/선호)은 `app/feedback/`, `app/preferences/`, `feedback.db` 에 있고, 그래프상 `feedback_seam` 노드 다음에 흡수 예정.
- 설계 상세: 루트 `docs/api-contract.md`, `docs/data-model.md`, `docs/agent-design.md`.

## 실행 (레포 루트 셸에서)

```bash
uv sync --directory backend --dev    # dev 그룹(pytest) 포함
uv run --directory backend fastapi dev app/main.py
uv run --directory backend pytest    # 테스트
```

`fastapi[standard]`에 uvicorn/fastapi-cli가 포함되므로 별도 추가하지 않는다.
저장소 경로는 `ACTION_ROUTER_DB_PATH` env var 로 바꿀 수 있다(기본 `backend/storage.db`).
FE 개발 서버 origin은 기본 `http://localhost:3000`, `http://127.0.0.1:3000`을 허용한다.
Tailscale 등 추가 origin은 `.env`의 `ACTION_ROUTER_CORS_ORIGINS`에 쉼표 구분으로 설정한다.
원격 기기 브라우저에서 접속할 때는 BE를 `--host 0.0.0.0`으로 열고, CORS origin에
`http://<tailscale-ip>:3000`을 추가한다.
시연/디버깅 로그는 `ACTION_ROUTER_LOG_LEVEL=DEBUG`로 상세화한다. 원문/LLM raw 응답까지
볼 때만 `ACTION_ROUTER_LOG_PAYLOADS=1`을 추가한다(키 값은 로깅하지 않음).
HITL은 LangGraph `interrupt()`+MemorySaver(thread_id=session_id)로, `/run`(정지) -> `/resume`(재개)로 표현한다.
시연용 기존 데이터는 `POST /mock/seed` 로 명시 초기화한다(일반 경로 자동 실행 없음).

## 의존성 정책

- 현재 의존성: `fastapi[standard]`, `langgraph`, `langchain-upstage`, `pydantic`.
- dev 의존성: `pytest`.
- `langchain-upstage`가 의존하는 `tokenizers==0.20.3` 빌드/휠 호환성 때문에 Python은 3.12 계열(`>=3.12,<3.13`)로 제한한다.

## 코드 스타일

- Python 들여쓰기는 PEP8 4 Spaces 로 통일한다(Tab 문자 미사용). CONTRIBUTING 확정 규칙.
- 결정 이력/배경은 `docs/decisions.md` 참조.

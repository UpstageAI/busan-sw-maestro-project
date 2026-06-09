# Decisions

변경/결정 이력을 담는다.

## 2026-06-05 - 코드 들여쓰기 규칙 확정 (Tab -> 4 Spaces)

- **확정: Python 들여쓰기는 PEP8 4 Spaces** (Tab 문자 미사용). CONTRIBUTING의 기존
  "Tab(=4 Spaces)" 규칙을 4 Spaces 로 변경. 기존 코드(backend, feat/preferences)가 이미
  스페이스이고 Python 표준이라 코드 변경은 없다. (이전까지 '미해결'이던 항목을 해결.)

## 2026-06-05 - 통합 토폴로지: 단일 LangGraph + interrupt HITL

- **확정: 6-1 -> 6-2 -> 6-3 를 하나의 LangGraph 로 통합한다.** 단계 간 핸드오프는
  `AgentState`(공유 상태). 사용자 개입(승인 등)은 LangGraph `interrupt()`로 그래프 중간에서
  정지하고, **checkpointer(MemorySaver) + thread_id(=session_id)** 로 상태를 보관했다가 재개한다.
- **HTTP 표현**: `POST /run`(시작 -> 승인 지점 interrupt) -> `POST /resume`(사용자 결정으로 재개).
  HITL이 있으므로 호출은 최소 2회. (대안이던 "단계별 HTTP 분리 / 무상태 2-call(/route,/approve)"는
  폐기. 흐름 제어와 상태를 그래프 한 곳에 모으기 위함.)
- **checkpointer = MemorySaver**(in-process, 데모용). 서버 재시작 시 세션 소멸. 영속 필요 시
  SqliteSaver 로 교체(의존성 추가).
- **6-3 연결부(seam)**: 6-2 그래프는 `feedback_entry` 노드에서 끝나고(현재 END), 6-3 담당자가
  그 뒤에 노드를 붙여 흡수한다. 6-2는 `final_output` + 수정 `(original, modified)` 쌍을 상태로 넘긴다.

## 2026-06-05 - 6-2 라우팅/검증/승인

- **저장소: SQLite 단일 파일 `backend/storage.db`** (테이블 분리). planning.md 정본이자
  feat/preferences의 SQLite 노선과 일관. 신규 의존성 0. 경로는 `ACTION_ROUTER_DB_PATH`
  env var / `configure_db_path()` 훅으로 주입 가능(테스트 격리).
- **Tool 선택 / 충돌 검사 LLM 미사용 (규칙 기반)**. type->tool 매핑, calendar 시간 겹침,
  task 제목 Jaccard>=0.6 + 담당자 + 마감 근접. LLM 보조는 `# TODO` 훅만(모델 미정).
- **승인 시 경량 재검증**: 실행 직전 `item.type`에서 tool 재도출 + 필수 필드 재확인. 누락/실패 시 Pending 폴백.
- **pytest를 `[dependency-groups] dev`로 추가** (런타임 의존성 아님). 실행:
  `uv run --directory backend pytest`.
- **feat/preferences `feedback.db`와 DB 통합은 6-3 그래프 흡수 시 재결정** (현재는 storage.db 단일).
- **seed는 데모 전용**: `POST /mock/seed` / 테스트 fixture에서만 실행. 일반 요청 경로
  자동 실행 금지("저장 전 사용자 승인" 제약과 구분되는 시연용 시스템 데이터).

## 미해결

- (없음)

## 프롬프트 변경 로그

작성 예정(다음 단계).

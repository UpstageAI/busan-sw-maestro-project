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

## 2026-06-08 - 저장된 선호 재주입(D3) 연결

- **`load_context()` 가 6-3 `feedback.db` 의 `load_user_preferences()` 를 호출**해 저장된
  선호를 `ContextBundle.preferences` 로 채운다. 그동안 stub(빈 컨텍스트)이라 저장만 되고
  분석에 반영되지 않던 경로(D3)를 연결. 읽기 함수/프롬프트 주입점은 이미 준비돼 있었고,
  비어있던 `load_context()` 만 채웠다.
- **선호 로드 실패는 분석을 막지 않는다**: DB 오류 시 빈 선호로 폴백(WARNING 로그)하고
  분석을 계속 진행한다. 선호가 실제로 주입될 때만 INFO 로그(시연 영상용 분기 기록).
- **후속(같은 브랜치에서 구현 완료)**: 기존 항목 요약 주입, Guideline(D4) JSON 주입,
  `_postprocess` 선호 코드 보정까지 이어서 채웠다. Context Loader stub 전반이 실데이터로 연결됨.

## 2026-06-08 - _postprocess 선호 코드 보정(이중 안전장치)

- LLM 출력(`AnalyzeResult.items`)을 코드가 한 번 더 검사해 저장된 선호대로 강제 치환한다.
  프롬프트 주입(D3)은 확률적이라 가끔 무시되므로, 코드 후보정으로 결정적 보장을 더한다.
- 필드값은 `model_dump(mode="json")` 기준으로 비교/치환하고 `Item.model_validate` 로 재검증해
  date/enum 타입을 강제한다(model_copy 의 무검증 치환 회피).

## 미해결

- (없음)

## 프롬프트 변경 로그

### 2026-06-08 - Solar 시스템 프롬프트: User Preference 반영 규칙 추가

- `app/llm/solar.py` `_SYSTEM` 에 규칙 1줄 추가. User Preference 가 주어지면 같은 field 에서
  입력이 해당 original_pattern 상황일 때 과거 선택값(preferred)을 기본값으로 반영하되,
  입력에 명시적 값이 있으면 입력을 우선하도록 명시.
- 배경: 선호가 프롬프트(human 메시지)에 실리고는 있었으나 활용 지시가 없어 LLM 이 무시할 수
  있었다. 재주입(D3) 연결과 함께 실제 반영되도록 규칙화.

### 2026-06-08 - Solar 시스템 프롬프트: Guideline 반영 규칙 추가

- `app/llm/solar.py` `_SYSTEM` 에 규칙 1줄 추가. Guideline 이 주어지면 분석/분류 시 그 지침을
  따르되 입력과 충돌하면 입력을 우선하도록 명시.
- 배경: D4 지침을 `guidelines.json` 으로 주입(`load_context`)하면서, User Preference 와 같은
  이유로 활용 지시를 프롬프트에 명시.

# Data Model

실행 항목/출력 JSON 스키마와 저장소(SQLite) 스키마를 담는다.

현재 정의된 범위: 6-2 라우팅/검증/승인(`backend/app/schemas/`, `backend/app/storage/`).
6-1 분석 출력 스키마는 6-2 입력(`Item`)으로 정의돼 있고, 6-3 선호 저장 스키마는
feat/preferences 브랜치(`feedback.db`)에 별도로 존재한다.

## 1. 항목 모델 (Pydantic)

정본: `backend/app/schemas/items.py`.

### Item (6-1 출력 = 6-2 입력)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | str \| null | 승인 추적용 식별자. 없으면 `/run`이 `item-{idx}` 부여 |
| type | ItemType | task / calendar / memo / risk / pending / ignore |
| title | str | 제목 (모든 type 필수) |
| assignee | str \| null | 담당자 (task) |
| due_date | date \| null | 마감일 (task) |
| date | date \| null | 일자 (calendar) |
| time | str \| null | "HH:MM" (calendar) |
| all_day | bool | 종일 일정 여부 (충돌 검사 제외 대상) |
| duration_estimate | int \| null | 분 단위 (calendar 충돌 검사용) |
| priority | Priority | high / medium / low (기본 medium) |
| content | str \| null | 메모 내용 (memo) |
| description | str \| null | 리스크 설명 (risk) |
| mitigation | str \| null | 대응 방안 (risk) |
| confidence | float | 6-1 확신도 (기본 1.0) |
| needs_confirmation | bool | 확인 필요 여부 |
| recommended_tool | ToolName \| null | 6-1이 주거나 6-2가 채움 |
| source_sentence | str \| null | 근거 문장 |
| clarification_question | str \| null | 확인 질문 (pending) |

### Enum

- `ItemType`: task, calendar, memo, risk, pending, ignore
- `ToolName`: create_task, create_calendar_event, create_memo, create_risk_log, save_to_pending
- `Priority`: high, medium, low

### Tool 별 필수 필드 (REQUIRED_FIELDS)

실행 직전 경량 재검증에 사용. 누락 시 Pending 폴백(status=failed).

| type | 필수 |
|------|------|
| task | title |
| calendar | title, date |
| memo | title |
| risk | title (description 없으면 title 로 대체) |
| pending | title |

## 2. 라우팅/승인 도메인 모델

정본: `backend/app/schemas/routing.py`, `backend/app/schemas/approval.py`.
전송(요청/응답) 모델은 `backend/app/schemas/run.py`(RunRequest/ResumeRequest/RunResponse), [api-contract.md](api-contract.md) 참조.

- **ToolSelection**: `{item_id, selected_tool, routing_reason}`
- **ConflictKind**: none / calendar_overlap / task_duplicate
- **ConflictAlternative**: merge / modify / pending (제안만, 자동 실행 없음)
- **ConflictCheckResult**: `{item_id, kind, has_conflict, conflicting_with[], warning, suggested_alternatives[]}`
- **ReviewableItem**: `{item, selection, conflict}` (승인 interrupt payload 구성 단위)
- **ApprovalAction**: approve / modify / exclude
- **ApprovalDecision**: `{item_id, action, modified_item?}` (승인 interrupt resume 입력)
- **ExecutionStatus**: success / failed / excluded / needs_recheck / pending
- **ExecutionResult**: `{item_id, status, tool, stored_id, error, recheck_required, modified_item?}`

## 3. 저장소 스키마 (SQLite)

정본: `backend/app/storage/db.py`. 단일 파일 `backend/storage.db`(테이블 분리).
경로는 `ACTION_ROUTER_DB_PATH` 환경변수 또는 `configure_db_path()` 훅으로 주입 가능.

```sql
tasks(id PK, title, assignee, due_date, priority, created_at)
calendar_events(id PK, title, date, time, all_day INT, duration_estimate, created_at)
memos(id PK, title, content, created_at)
risk_logs(id PK, description, mitigation, created_at)
pending_queue(id PK, title, reason, clarification_question, created_at)
```

저장소 매핑(Tool -> table): create_task->tasks, create_calendar_event->calendar_events,
create_memo->memos, create_risk_log->risk_logs, save_to_pending->pending_queue.

> 6-3(feat/preferences)의 `feedback.db`(preference_candidate_log, user_preference)와는 현재 별도 파일이다.
> DB 통합 여부는 6-3 병합 시 재결정한다([decisions.md](decisions.md) 참조).

## 4. Mock 데이터

6-2 단독 테스트/데모에서 `/analyze/` 결과 Item 입력을 대신한다. 정본: `backend/app/mock_data/sample_inputs.py`.
기준일 2026-06-05 고정. 시나리오 3종: `multi`(다항목), `vague_risk`(보류+리스크), `conflict`(일정 충돌).

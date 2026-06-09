# API Contract

FE <-> BE 간 HTTP 계약. 스키마 상세는 [data-model.md](data-model.md), 흐름은 [agent-design.md](agent-design.md) 참조.

정본 구현: `backend/app/api/routes/run.py`. 6-3(피드백/선호)의 `/feedback/*`, `/confirm`은
feat/preferences 에서 별도 정의되며, 향후 같은 그래프로 흡수 예정([agent-design.md](agent-design.md) 6-3 seam).

## 동기식 승인 = 단일 그래프 interrupt/resume

6-1~6-2~6-3 를 하나의 LangGraph 로 잇고, 사용자 개입 지점(승인)에서 `interrupt()`로 정지한다.
상태는 checkpointer(MemorySaver)에 `thread_id`(=`session_id`)로 보관됐다가 재개된다.

1. `POST /run` -> 그래프 시작. 승인 지점에서 정지하고 검토 패키지(reviewables)를 반환(`status=awaiting_approval`).
2. 사용자가 항목별 승인/수정/제외 결정.
3. `POST /resume` -> 결정으로 그래프 재개. Tool 실행 후 종료(`status=completed`).

> HITL이 있으므로 호출은 최소 2회(run -> resume)다. 향후 6-3가 그래프에 붙으면 선호 확인 지점에서
> interrupt가 한 번 더 생겨 resume가 추가될 수 있다(같은 session_id 로 이어짐).

## 엔드포인트

### GET /health
- 응답: `{"status": "ok"}`

### POST /analyze/
6-1 분석 단계 단독 엔드포인트. 비정형 텍스트를 받아 6-2 `Item` 계약에 맞는 실행 항목 배열을 반환한다.
저장/Tool 실행은 하지 않는다.

요청:
```json
{
  "raw_text": "내일까지 성종은 발표자료, 금요일 오전 10시 최종 리허설하자.",
  "base_date": "2026-06-05"
}
```

응답:
```json
{
  "items": [
    {
      "type": "task",
      "title": "발표자료 준비",
      "assignee": "성종",
      "due_date": "2026-06-06",
      "date": null,
      "recommended_tool": "create_task",
      "confidence": 0.95,
      "needs_confirmation": false
    }
  ]
}
```

### POST /run
6-1 Item(`/analyze/` 출력 또는 데모 샘플)을 받아 그래프 시작. 승인 지점에서 정지.

요청 (RunRequest):
```json
{
  "session_id": "demo-conflict",
  "items": [
    {"type": "calendar", "title": "팀 회의", "date": "2026-06-09", "time": "10:00", "duration_estimate": 60}
  ]
}
```
- `session_id` 는 그래프 세션(thread_id). resume 시 동일 값 사용.
- `items` 는 `/analyze/` 출력 Item. 현재 FE 흐름은 `/analyze/` -> `/run` 순서다.
- `raw_input`(비정형 텍스트) 필드는 향후 `/run` 단일 호출로 직접 분석할 때 사용할 확장 자리다.

응답 (RunResponse, awaiting_approval):
```json
{
  "session_id": "demo-conflict",
  "status": "awaiting_approval",
  "reviewables": [
    {
      "item": {"id": "item-0", "type": "calendar", "title": "팀 회의", "date": "2026-06-09", "time": "10:00", ...},
      "selection": {"item_id": "item-0", "selected_tool": "create_calendar_event", "routing_reason": "일정 항목 -> 캘린더 이벤트 생성"},
      "conflict": {
        "item_id": "item-0", "kind": "calendar_overlap", "has_conflict": true,
        "conflicting_with": [{"id": 1, "title": "기존 스프린트 회의", ...}],
        "warning": "2026-06-09 10:00 시간대에 기존 일정 1건과 겹칩니다.",
        "suggested_alternatives": ["modify", "pending"]
      }
    }
  ],
  "skipped": [],
  "results": [], "summary": {}, "final_output": null
}
```
- `id` 가 없으면 서버가 `item-{idx}` 부여. `type=ignore` 는 `skipped`.
- 검토 대상이 없으면(전부 ignore) 승인 없이 `status=completed` 로 바로 끝난다.

### POST /resume
승인 interrupt 에 대한 사용자 결정으로 그래프 재개.

요청 (ResumeRequest):
```json
{
  "session_id": "demo-conflict",
  "decisions": [
    {"item_id": "item-0", "action": "approve"},
    {"item_id": "item-1", "action": "exclude"},
    {"item_id": "item-2", "action": "modify", "modified_item": {"id": "item-2", "type": "task", "title": "수정본", ...}}
  ]
}
```
응답 (RunResponse, completed):
```json
{
  "session_id": "demo-conflict",
  "status": "completed",
  "reviewables": [], "skipped": [],
  "results": [
    {"item_id": "item-0", "status": "success", "tool": "create_calendar_event", "stored_id": 2},
    {"item_id": "item-1", "status": "excluded"},
    {"item_id": "item-2", "status": "needs_recheck", "recheck_required": true, "modified_item": {...}}
  ],
  "summary": {"executed": 1, "excluded": 1, "failed": 0, "recheck": 1},
  "final_output": { "summary": {...}, "executed": [...], "excluded": [...], "pending": [...], "needs_recheck": [...] }
}
```

#### action 의미
- `approve`: 실행 직전 `item.type`에서 tool 재도출(echo 불신) + 필수 필드 재확인 -> Tool 실행 + 저장.
  status `success` (Tool 실패 시 `pending`, 필수 필드 누락 시 `failed`, 둘 다 Pending 폴백).
- `exclude`: 저장하지 않음 -> `excluded`.
- `modify`: 저장하지 않고 `modified_item` 을 결과에 담음 -> `needs_recheck`(`recheck_required=true`).
  수정 쌍(original, modified)은 6-3 Feedback Analyzer 로 전달된다([agent-design.md](agent-design.md) 6-3 seam).

### GET /storage/{kind}
저장소 행 조회 (데모 확인용). kind: tasks / calendar_events / memos / risk_logs / pending_queue.
- 응답: `{"kind": "...", "count": N, "rows": [...]}` / 알 수 없는 kind: 404.

### POST /mock/seed  (데모 전용)
시연용 시스템 데이터 초기화. **운영/일반 사용자 흐름이 아니다.** 루트 지침의 "저장 전 사용자 승인"
대상과 무관한 시연용 시스템 데이터(충돌 검증용 기존 일정/작업)를 멱등하게 넣는다.
- 응답: `{"seeded": {"calendar_events": N, "tasks": N}}`

### POST /mock/run/{scenario}  (데모 전용)
Mock 시나리오 입력을 `/run` 으로 흘려보내는 데모 트리거. scenario: multi / vague_risk / conflict.
- 응답: RunResponse. / 알 수 없는 scenario: 404.

## 6-3 엔드포인트 (feat/preferences, 별도)
`/feedback/analyze`, `/feedback/confirm`, `/confirm/` 은 현재 별도 라우터로 공존한다.
단일 그래프 통합 후에는 승인 이후 흐름이 그래프 내부(interrupt)로 들어와 별도 호출이 줄어들 수 있다.

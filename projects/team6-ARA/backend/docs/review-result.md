# 코드 리뷰 결과

리뷰 도구: LangGraph 공식 스킬(human-in-the-loop / persistence) + Context7(LangGraph/FastAPI 문서 대조) + built-in code-review(7개 finder 교차검증) + security 관점.

## 1라운드 - feat/routing-agent-api (커밋 c6065ce, 2026-06-06)

범위: 6-1~6-2 단일 LangGraph (interrupt HITL) + /run, /resume. 18파일.

### 검증 통과 (문제 없음)

- LangGraph HITL 패턴이 공식 문서/스킬과 일치: interrupt() -> `__interrupt__` surface -> Command(resume=) -> interrupt() 반환. checkpointer(MemorySaver) + thread_id(session_id).
- 멱등성 안전: approval_node 의 interrupt 앞에는 로깅만, 실제 쓰기(tool 실행/DB 저장)는 interrupt 이후 execution_node. resume 재실행 시 중복 side effect 없음.
- FastAPI lifespan(asynccontextmanager + init_db) 구조가 공식 권장과 일치.
- SQL injection 안전: list_table 의 f-string `table` 은 사용자 입력(kind)이 아니라 TABLES 화이트리스트 매핑값.

### 수정 완료

| # | 등급 | 위치 | 내용 | 처리 |
|---|------|------|------|------|
| 1 | 버그(CONFIRMED, repro) | `logging_config.py` | `ACTION_ROUTER_LOG_LEVEL` 소문자(debug/info) 설정 시 setLevel ValueError 로 앱 부팅 crash. | env/인자 문자열을 `.upper()` 정규화. |
| 2 | 중 | `execution.py` `_execute_one` | approve+modified_item 시 결과 item_id 를 `item.id or ""` 로 잡아 FE 가 id 를 비우면 결과-원본 매칭 끊김. | `decision.item_id` 를 명시 인자로 전달(modified_item.id 불신). |
| 3 | 중 | `execution.py` 필수필드 누락 폴백 | status=failed 인데 save_to_pending 으로 행은 저장됨(의미 불일치). tool 실패 폴백은 이미 pending. | status를 pending 으로 통일(저장됨=pending). 테스트 단언도 갱신. |
| 4 | 낮 | `run.py` `mock_run` | 고정 session_id 재사용 + 프로세스 지속 MemorySaver 로 같은 시나리오 재시연 시 이미 interrupt 된 thread 재진입. | 매 호출 고유 session_id(`base-<uuid8>`) 부여. 응답 session_id 로 resume. |

### 주석으로 가정 고정 (데모 범위에서 의도된 단순화)

| 위치 | 가정 | 운영 전환 시 |
|------|------|--------------|
| `graph.py` build_graph | 단일 워커 전제. `@lru_cache`+`MemorySaver()` 는 프로세스 인메모리/스코프 -> 다중 워커(--workers N)/dev 리로드 시 /run 과 /resume 이 다른 프로세스에 분배되면 resume 실패, 재시작 시 진행 세션 소실. | SqliteSaver/PostgresSaver 로 교체. |
| `run.py` `_to_response` | interrupts[0] 단일 interrupt 전제(approval 노드 1개). | 병렬/추가 interrupt 생기면 id 별 매핑 필요. |
| `run.py` `resume` | 해당 session_id 가 승인 interrupt 로 정지된 상태 전제(happy path). 정지 아님/없음/중복 resume 시 동작 미보장. | 대기 세션 존재 검증(graph.get_state) 후 없으면 4xx 반환. |

### 후순위 (건너뜀: 큰 리팩 또는 forward-looking, 데모 범위 밖)

| 위치 | 내용 | 사유 |
|------|------|------|
| `execution.py` `_build_kwargs` | 툴별 인자를 if-체인 하드코딩 -> `local_tools.py` 시그니처와 이중 관리. 필드 추가 시 한쪽 누락하면 silent drop. | 시그니처 기반 매핑/per-tool builder 로 일반화 필요(구조 변경). |
| 다수 (`TYPE_TO_TOOL`/`REQUIRED_FIELDS`/`_build_kwargs`/`check_conflict`) | ItemType 지식이 4곳에 분산. 타입 추가 시 4곳 동기화. | per-type descriptor(tool+required+kwargs+conflict)로 통합 필요(구조 변경). |
| `execution.py` modify 경로 | needs_recheck 신호만 주고 conflict_check 재검증 없이 END dead-end. 수정으로 새 충돌 생겨도 미검출. | 수정 항목을 그래프에 재투입하는 loopback 설계 필요(6-1 재검증 계약 확정 후). |
| `state.py` AgentState | Annotated reducer 없음. 현재 선형 그래프라 안전하나, 향후 parallel fan-out 으로 두 노드가 같은 key 쓰면 InvalidUpdateError. | fan-out 도입 시 해당 key 에 reducer 추가. |
| `run.py` `/storage/{kind}`, `/mock/run` 404 detail | 내부 테이블/시나리오 이름을 에러 메시지로 노출(정보 노출). | 내부 데모 API 라 경미. 외부 노출 시 일반화된 메시지로. |
| `schemas/run.py` RunResponse | summary(dict)/final_output(dict\|None) 무타입 passthrough -> 비 JSON 값 stash 시 직렬화 오류 가능. | 6-3 계약 확정 후 타입 모델로 승격. |
| `analysis.py` | `/run`에 raw_input 만 오고 items 없으면 빈 items 반환 -> 전체 silent no-op(WARNING 로그만). | 현재 FE는 `/analyze/` -> `/run` 순서라 정상 경로는 안전. `/run` 단일 호출 분석을 열면 4xx 또는 분석 연결 필요. |
| `conflict_check.py` | `{it["id"]: ...}` 가 모든 item 에 id 존재 가정(KeyError latent). tool_selection 이 항상 ensure_id 하므로 현재 안전. | 노드 간 암묵 순서 의존. 직접 호출/테스트 시 주의. |
| `conflict_check.py` | calendar/task 항목이 없어도 load_calendar_events + load_tasks 무조건 호출(불필요 I/O). | 효율 minor. selections 타입에 따라 지연 로드 가능. |

## 2라운드 - main 의 6-2 파트 (커밋 8166c03, 2026-06-07)

범위: sjPark 가 개발해 main 에 머지된 6-2 "토대" 코드만. 그 위에 얹힌 그래프/노드/API 레이어는
1라운드에서 이미 봤으므로 제외. 대상 8파일: `conflict/rules.py`, `schemas/{items,routing,approval}.py`,
`storage/{db,queries,seed}.py`, `tools/local_tools.py`.
교차검증: 수동 리뷰 + 독립 code-reviewer 에이전트 + docs/data-model.md 계약 대조 + Context7(Pydantic v2 대조).

### 검증 통과 (문제 없음)

- 충돌 겹침 판정 `new_start < ev_end and ev_start < new_end` 는 표준 인터벌 겹침 공식으로 정확.
- 마감일 근접(+-1일) 판정: 둘 다 있으면 abs 일수 비교, 한쪽만 있으면 비중복, 둘 다 없으면 근접 간주 - docstring 과 정합.
- risk 의 `REQUIRED_FIELDS[risk]=("title",)` 는 execution `_build_kwargs` 가 `item.description or item.title`
  로 NOT NULL 컬럼을 채우므로 정합(IntegrityError 아님).
- `list_table` f-string 의 table 명은 TABLES 화이트리스트 값(사용자 입력 아님) -> SQL injection 안전.
- `_parse_hhmm` 는 "25:00"/"10:61" 등 비정상 시간을 strptime ValueError 로 걸러 None 반환.
- 스키마(items/routing/approval)는 data-model.md 계약과 필드/Enum 일치(드리프트 없음).
- (Context7/Pydantic v2 대조) `model_config={"use_enum_values": False}` 는 Pydantic 기본값과 동일하나, `_build_kwargs` 의 `item.priority.value` 접근이 깨지지 않도록 동작을 못박는 의미 있는 가드(True 면 .value AttributeError). str-Enum 은 JSON mode 에서 항상 value 로 직렬화되어 `model_dump(mode="json")` 응답이 JSON-safe. `Field(default_factory=list)` 는 mutable default 권장 패턴과 일치.

### 수정 완료

| # | 등급 | 위치 | 내용 | 처리 |
|---|------|------|------|------|
| 1 | 버그(repro) | `storage/db.py` `get_conn` | `with get_conn() as conn:` 가 sqlite3.Connection 의 CM 를 쓰는데, 이 CM 은 commit/rollback 만 하고 close 를 안 해 호출마다 커넥션 누수. queries/seed/local_tools 전 호출처에 해당. | `get_conn` 을 `@contextmanager` 로 바꿔 finally 에서 close. `init_db` 의 `get_conn().close()` 는 `with get_conn(): pass` 로 변경. 쓰기 함수의 명시 commit 은 유지. repro 로 블록 종료 후 닫힘 확인. |
| 2 | 경미(계약 정합) | `conflict/rules.py` `_parse_date` | 입력 타입이 `Any` 인데 datetime 이 date 서브클래스라 isinstance(date) 를 통과 -> date 와 == 비교 어긋남(현재 경로엔 datetime 유입 없어 미재현, 함수 자체 계약 결함). | datetime 을 먼저 `.date()` 로 떨구도록 가드 추가(현재 동작 불변, 순수 하드닝). |

### 주석으로 가정 고정

| 위치 | 가정 | 운영 전환 시 |
|------|------|--------------|
| `rules.py` `check_calendar_conflict` | 같은 날짜 안에서만 겹침 판정(자정 넘김 미처리). 23:00+120분이 다음 날로 흘러도 다음 날 일정과 대조 안 함. 데모 60분 일정에선 미발생. | 다중일 인터벌 모델 필요(아래 후순위). |

### 후순위 (건너뜀: 데모 범위 밖 또는 forward-looking)

| 위치 | 내용 | 사유 |
|------|------|------|
| `rules.py` 자정 경계 | 자정 넘기는 일정 겹침 미검출(위 주석으로 가정 고정). | "자정 기준 분 + 같은 날짜" 모델의 본질 한계. 다중일 인터벌은 설계 변경. 데모 미발생. |
| `rules.py` `check_task_duplicate` | 제목은 normalize(lower/공백정리)하지만 assignee 는 원문 비교 -> "박성종" vs "박성종 " 불일치 가능. | 정규화 불일치(경미). 입력이 6-1 정형 출력이라 현재 영향 낮음. |
| 6-3 모듈 `feedback/db.py`, `preferences/store.py` `_get_conn` | 위 #1 과 동일한 커넥션 누수 패턴(별도 함수). | hyeonZIP 의 6-3 코드라 2라운드(sjPark 6-2) 범위 밖. 3라운드(전체) 또는 소유자 수정 대상. |
| `routing.py` `ConflictCheckResult.conflicting_with` | `list[dict]` 무타입 passthrough(기존 DB 행). | 1라운드 summary/final_output 무타입 노트와 동류. 현재 값은 전부 JSON 직렬화 가능해 안전. |

## 3라운드 - 전체 리뷰 (예정)

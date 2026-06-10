# Phase 2 · 1단계 완료 보고 — LangGraph 워크플로우 조립

> 담당: donghakk (통합 오너) · 브랜치: `feat/integration` · 커밋: `ebe0334`

## 한 줄 요약
개별로만 완성돼 있던 노드 1~4를 **LangGraph `StateGraph`로 배선**해, 단일 진입점에서
입력을 받아 프론트 계약(`final_response`)을 산출하는 컴파일된 그래프를 만들었습니다.

## 배경
- 각 노드(`parse_input`, `interview_gap_node`, `mentor_retrieval_node`, `fit_evaluation_node`,
  `query_refiner_node`, `result_builder_node`)는 함수로는 완성돼 있었으나 **이어주는
  오케스트레이션 코드가 없었습니다**. `langgraph`는 import조차 안 된 상태.
- Phase 2(노드1~4 + 프론트 E2E 마감)의 임계 경로 — API 서버·프론트가 이 위에 얹힙니다.

## 변경 사항
| 파일 | 내용 |
|---|---|
| `backend/app/graph/workflow.py` (신규) | `build_graph()` — StateGraph 조립/compile, `clarification_node`, 분기 라우터 2개, `MAX_RETRY=1` |
| `requirements.txt` (신규) | 의존성 매니페스트 신설 — `langgraph==1.2.4`, `pydantic`, `pytest` |
| `tests/test_workflow.py` (신규) | E2E + 라우터 단위 테스트 6개 |

> **타 작업자 노드 파일은 무수정.** 명명 불일치(`parse_input` vs `*_node`)는 함수를 고치지
> 않고 그래프 노드명(`input_parser`)으로 흡수했습니다.

## 그래프 흐름
```
START → input_parser ─┬─ (입력 부족) → clarification → END
                      └─ (충분)      → interview_gap → mentor_retrieval
                                        → fit_evaluation ─┬─ (신뢰)        → result_builder → END
                                                          ├─ (저신뢰·재시도) → query_refiner → mentor_retrieval
                                                          └─ (저신뢰·소진)   → result_builder → END
```
- **분기 1 (입력 충분성)**: 노드1 `is_input_sufficient` → 부족 시 확인 질문으로 조기 종료.
- **분기 2 (추천 신뢰도)**: 노드3 `is_recommendation_confident` → 저신뢰면 `query_refiner`로
  쿼리 보강 후 재검색(최대 `MAX_RETRY=1`회), 소진 시 `limited` 산출.
- 그래프가 status 3종 모두에 대해 `final_response`를 산출 → 2단계 서버를 얇게 유지.

## 검증
- **테스트 6개 신규 + 기존 79개 = 85개 전부 통과**, 회귀 0.
- `langgraph 1.2.4`가 **Python 3.14에서 정상 설치/동작** (호환성 리스크 해소).
- 재현:
  ```bash
  pip install -r requirements.txt
  pytest tests/test_workflow.py -v
  ```

## ⚠️ 공유 필요 — 알아두실 점
**limited/retry 경로는 현재 규칙 기반 모드에서 자연 입력으로는 도달하지 않습니다.**
- `fit_evaluation`이 **max-정규화**로 최고점을 항상 100으로 만들어, 후보가 1명이라도 있으면
  `is_recommendation_confident`(max≥60)가 항상 참이 됩니다.
- 게다가 BM25는 항상 후보를 반환하고, gap 분석도 항상 매칭 카테고리로 폴백 → 검색이 비지 않음.
- → **배선 자체는 정상**이며, 이 경로는 멘토 DB가 비거나 **나중에 LLM을 붙여 점수가 분산되면**
  작동합니다. (테스트는 빈 멘토 DB로 루프를 결정적으로 검증)
- **노드3 담당께**: LLM swap-in 시 점수 분산이 생기면 재검색 루프가 실제로 활성화됩니다.

## 다음 단계
→ 2단계: FastAPI `/recommend` 서버 + 인메모리 세션.

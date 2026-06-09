# docs AGENTS.md

문서 맵(에이전트용). 각 문서가 무엇이고 언제 보는지 한 줄씩.

상위 참조: 전체 구조/문서 맵은 루트 AGENTS.md / README.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

- `planning.md` - 기획서. 작업 시작 전 범위/목표 확인용(필수 참조).
- `api-contract.md` - FE <-> BE HTTP 계약. 엔드포인트/요청/응답 정의할 때.
- `data-model.md` - 항목/출력 JSON 스키마 + 저장소 스키마. 데이터 구조 정할 때.
- `agent-design.md` - LangGraph 흐름 + LLM 입출력 계약 + 모델 선택 + 외부연동(향후). Agent 로직 설계할 때.
- `decisions.md` - 변경/결정 이력 + 프롬프트 변경 로그. 결정 남기거나 배경 확인할 때.
- `prompts/` - 프롬프트 텍스트 보관(콘텐츠 폴더, README만).
- `samples/` - 데모 시나리오 입력/기대출력 보관(콘텐츠 폴더, README만).

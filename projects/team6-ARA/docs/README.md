# docs

Action Router Agent의 설계/계약/결정 문서 인덱스(사람용).

상위 참조: 전체 구조/문서 맵은 루트 README.md / AGENTS.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

## 문서 목록

- `planning.md` - 기획서(과제 정의/범위/시나리오). ※ 작성자가 직접 관리.
- `api-contract.md` - FE <-> BE HTTP 계약.
- `data-model.md` - 항목/출력 JSON 스키마 + 저장소 스키마.
- `agent-design.md` - LangGraph 흐름 + LLM 입출력 계약 + 모델 선택 + 외부연동(향후).
- `decisions.md` - 변경/결정 이력 + 프롬프트 변경 로그.
- `prompts/` - 프롬프트 텍스트 보관(안정화 후 backend로 이전 예정).
- `samples/` - 데모 시나리오 입력/기대출력 보관(안정화 후 backend/tests로 이전 예정).

# AGENTS.md (루트 정본)

Action Router Agent 모노레포의 에이전트용 정본. 전체 지도만 담는다. 세부 내용은 각 docs 파일로 가리킨다
(본문 복붙 금지, 드리프트 방지).

## 폴더 구조와 역할

- `frontend/` - React. 실행법/구조는 `frontend/AGENTS.md` 참조.
- `backend/` - FastAPI + LangGraph Agent 백엔드. 실행법/구조는 `backend/AGENTS.md` 참조.
- `docs/` - 설계/계약/결정 문서. 문서별 용도는 `docs/AGENTS.md` 참조.

## 확정 / 미정 스택

- 확정: Python / FastAPI(BE) / LangGraph / Pydantic / React(CRA)(FE).
- 미정: Agent용 LLM(Solar 유력), 저장소(SQLite or JSON).

## 핵심 제약

- 범위 제외: 외부 실시간 연동, 배포, Vector RAG, 멀티에이전트.
- 데이터를 저장하기 전에는 반드시 사용자 승인을 받는다.

## 실행 원칙

- 에이전트는 레포 루트에서 기동하고, 코드 실행 위치도 루트로 통일한다.
- backend 실행: 루트 셸에서 `uv run --directory backend fastapi dev app/main.py`
  (`--directory`는 서브프로세스 cwd만 backend로 옮김. 루트 셸은 유지.)

## 문서 맵

- `docs/planning.md` - 기획서(작업 시 필수 참조).
- `docs/api-contract.md` - FE <-> BE HTTP 계약.
- `docs/data-model.md` - 항목/출력 JSON 스키마 + 저장소 스키마.
- `docs/agent-design.md` - LangGraph 흐름 + LLM 입출력 계약 + 모델 선택 + 외부연동(향후).
- `docs/decisions.md` - 변경/결정 이력 + 프롬프트 변경 로그.
- `docs/prompts/` - 프롬프트 텍스트 보관.
- `docs/samples/` - 데모 시나리오 입력/기대출력 보관.
- `.github/CONTRIBUTING.md` - 브랜치/커밋/코드스타일 규칙(정본).
- `.github/PULL_REQUEST_TEMPLATE.md` - PR 양식.

## 갱신 규칙

- 전체 구조/폴더 역할/문서 맵이 바뀌면 이 루트 문서를 갱신한다.
- 특정 폴더 내부만 바뀌면 해당 폴더의 AGENTS.md / README.md를 갱신한다.

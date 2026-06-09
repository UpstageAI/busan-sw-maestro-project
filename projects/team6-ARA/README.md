# asm-team06-ai-study - Action Router Agent

비정형 텍스트에서 실행 항목을 추출/분류하고 적절한 Tool로 라우팅하는 Action Router Agent 로컬 데모.
소마 AI 기술교육용 3주 과제 레포다.

## 모노레포 구조

- `frontend/` - React(CRA) 사용자 인터페이스.
- `backend/` - FastAPI + LangGraph 기반 Agent 백엔드.
- `docs/` - 설계/계약/결정 문서.

## 문서 맵

- `docs/planning.md` - 기획서(과제 정의, 범위, 시나리오). ※ 작성자가 직접 관리.
- `docs/api-contract.md` - FE <-> BE HTTP 계약.
- `docs/data-model.md` - 항목/출력 JSON 스키마 + 저장소 스키마.
- `docs/agent-design.md` - LangGraph 흐름 + LLM 입출력 계약 + 모델 선택 + 외부연동(향후).
- `docs/decisions.md` - 변경/결정 이력 + 프롬프트 변경 로그.
- `docs/prompts/` - 프롬프트 텍스트 보관(안정화 후 backend로 이전 예정).
- `docs/samples/` - 데모 시나리오 입력/기대출력 보관(안정화 후 backend/tests로 이전 예정).
- `.github/CONTRIBUTING.md` - 브랜치/커밋/코드스타일 규칙(정본).
- `.github/PULL_REQUEST_TEMPLATE.md` - PR 양식.

## 스택 / 범위

- 확정: Python / FastAPI / LangGraph / Pydantic / React(CRA) / SQLite.
- LLM: 6-1 분석 단계는 Upstage Solar를 우선 사용하고, 키가 없으면 FakeLLM으로 폴백한다.
- 현재 범위 제외: 외부 실시간 연동, 배포, Vector RAG, 멀티에이전트.

## 실행 방법

레포 루트 셸에서 실행한다. `uv`가 PATH에 없으면 먼저 `export PATH="$HOME/.local/bin:$PATH"`를 실행한다.

```bash
# backend 의존성 설치
uv sync --directory backend --dev

# backend 개발 서버
uv run --directory backend fastapi dev app/main.py

# frontend 개발 서버
npm install --prefix frontend
npm start --prefix frontend
```

기본 접속:

- FE: `http://localhost:3000`
- BE health: `http://localhost:8000/health`

`--directory backend`는 서브프로세스의 작업 디렉토리만 backend로 옮긴다. 사람과 에이전트는 레포 루트 셸을 유지한다.

### Solar API / 로그

Solar 실연동은 backend 실행 터미널에서 환경변수로 설정한다.

```bash
export UPSTAGE_API_KEY="..."
export LLM_PROVIDER=solar
export ACTION_ROUTER_LOG_LEVEL=DEBUG

uv run --directory backend fastapi dev app/main.py
```

원문과 Solar raw 응답까지 로그로 보고 싶을 때만 `ACTION_ROUTER_LOG_PAYLOADS=1`을 추가한다.

## 현재 데모 흐름

1. FE 입력 화면에서 회의록/메모/공지사항을 붙여넣는다.
2. `POST /analyze/`: 6-1 분석. Solar 또는 FakeLLM이 실행 항목 후보를 만들고, 코드가 confidence/completeness를 산정한다.
3. `POST /run`: 6-2 라우팅, 충돌/중복 검증, 승인 대기 패키지를 만든다.
4. FE 승인 화면에서 항목을 승인/수정/제외한다.
5. `POST /resume`: 승인된 항목만 SQLite 저장소에 저장한다.
6. `GET /storage/{kind}`: 저장소 탭에서 실제 저장 결과를 확인한다.

3단계 선호 확인 UI는 아직 목데이터 구간이다. `/feedback/analyze`, `/feedback/confirm` API는 존재하지만 FE 모달에는 완전히 연결되지 않았다.

## 테스트

```bash
uv run --directory backend pytest
npm run build --prefix frontend
```

## 개인 지침 설정

팀원 각자 `~/.claude/action-router.md`를 만들면 루트 `CLAUDE.md`가 이를 자동 import한다(개인 작업 규칙 레이어).
이 파일은 레포에 커밋되지 않는다. 파일이 없어도 설정은 깨지지 않으며, 개인 레이어만 로드되지 않을 뿐이다
(첫 실행 시 import 승인 1회 필요).

## 에이전트 실행 규칙

- AI 에이전트(Claude Code / Codex)는 반드시 레포 루트에서 기동하고, 코드 실행 위치도 루트로 통일한다.
- 전체 구조/폴더 역할/문서 맵이 바뀌면 이 루트 문서(README.md / AGENTS.md)를 갱신한다.
  특정 폴더 내부만 바뀌면 해당 폴더의 AGENTS.md / README.md를 갱신한다.

# frontend AGENTS.md (frontend 정본)

React 기반 Action Router Agent 프론트엔드.

상위 참조: 전체 구조/문서 맵은 루트 AGENTS.md / README.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

## 구조

- `src/` - React 컴포넌트 및 페이지.
- `src/index.js` - 앱 진입점.
- `src/App.js` - 루트 컴포넌트.
- API 호출 로직은 `src/api/`에, 공통 컴포넌트는 `src/components/`에 둔다.

## 실행 (레포 루트 셸에서)

```bash
npm install --prefix frontend
npm start --prefix frontend
```

또는 frontend 디렉토리 안에서:

```bash
npm install
npm start
```

개발 서버는 기본 `http://localhost:3000`에서 실행된다.

## 의존성 정책

- 현재 의존성: `react`, `react-dom`, `react-scripts`, `styled-components`.
- 상태 관리/라우팅 라이브러리는 필요 시 추가하고 `docs/decisions.md`에 기록한다.
- BE API 주소는 `.env`의 `REACT_APP_API_URL`로 관리한다.
  기본값은 현재 접속한 FE 호스트의 8000번 포트다
  (예: `http://localhost:3000` -> `http://localhost:8000`,
  `http://<tailscale-ip>:3000` -> `http://<tailscale-ip>:8000`).

## 코드 스타일

- JavaScript(`.js` / `.jsx`) 사용.
- 들여쓰기: 스페이스 4칸 (CRA 기본 기준).
- 팀 합의 전까지 위 기준으로 작성하고, 변경 시 `docs/decisions.md`에 기록한다.

# frontend

FE 스택: React(CRA) 기반 Action Router Agent 프론트엔드.

상위 참조: 이 레포는 모노레포이며, 전체 구조/문서 맵은 루트 README.md / AGENTS.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

## 실행

레포 루트에서 실행한다.

```bash
npm install --prefix frontend
npm start --prefix frontend
```

기본 개발 서버는 `http://localhost:3000`이다.

Tailscale 등 원격 브라우저에서 미니PC의 FE에 접속할 때:

```bash
HOST=0.0.0.0 npm start --prefix frontend
```

브라우저에서는 `http://<mini-pc-tailscale-ip>:3000`으로 접속한다.

## API 연결

`REACT_APP_API_URL`이 있으면 그 값을 사용한다. 없으면 현재 접속한 FE 호스트의 8000번 포트를 기본 BE 주소로 사용한다.

예:

- `http://localhost:3000` -> `http://localhost:8000`
- `http://<tailscale-ip>:3000` -> `http://<tailscale-ip>:8000`

명시적으로 지정하려면:

```bash
REACT_APP_API_URL=http://localhost:8000 npm start --prefix frontend
```

## 현재 화면 흐름

1. 입력: `/analyze/`와 `/run` 호출.
2. 분석·승인: `/resume` 호출.
3. 선호 확인: 현재 목데이터 UI.
4. 결과 요약: `/resume` 결과 표시.
5. 저장소 보기: `/storage/{kind}` 호출. preferences 탭은 목데이터.

## 빌드

```bash
npm run build --prefix frontend
```

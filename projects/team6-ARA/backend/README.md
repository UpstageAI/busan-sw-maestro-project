# backend

FastAPI + LangGraph 기반 Action Router Agent 백엔드. backend 단독 uv 프로젝트다.

상위 참조: 전체 구조/문서 맵은 루트 README.md / AGENTS.md에 있다. 폴더 밖 맥락은 루트 문서를 참조한다.
갱신 규칙: 이 폴더의 구조나 역할이 바뀌면 이 파일을 갱신한다.

## 실행 (레포 루트 셸에서)

```bash
# 의존성 설치(.venv + uv.lock 생성)
uv sync --directory backend --dev

# 개발 서버 기동 (GET /health -> {"status":"ok"})
uv run --directory backend fastapi dev app/main.py

# 테스트
uv run --directory backend pytest
```

`--directory backend`는 서브프로세스 cwd만 backend로 옮긴다. 사람과 에이전트는 루트 셸을 유지한다.

## 주요 API

- `POST /analyze/` - 6-1 분석. 비정형 텍스트를 Item 배열로 변환.
- `POST /run` - 6-2 그래프 시작. 라우팅/충돌검사 후 승인 대기.
- `POST /resume` - 승인 결정으로 그래프 재개. 승인 항목 저장.
- `GET /storage/{kind}` - SQLite 저장소 조회.
- `POST /mock/seed`, `POST /mock/run/{scenario}` - 데모 전용.
- `POST /feedback/analyze`, `POST /feedback/confirm`, `POST /confirm/` - 6-3 피드백/선호 API.

## 환경변수

```bash
export UPSTAGE_API_KEY="..."              # Solar API 키
export LLM_PROVIDER=solar                 # solar 강제. 미설정+키 없음이면 FakeLLM
export SOLAR_MODEL=solar-pro              # 선택
export ACTION_ROUTER_LOG_LEVEL=DEBUG      # INFO/DEBUG/WARNING/ERROR
export ACTION_ROUTER_LOG_PAYLOADS=1       # 원문/LLM raw 응답 로깅. 필요할 때만
export ACTION_ROUTER_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export ACTION_ROUTER_DB_PATH="/tmp/action-router.db"
```

Tailscale 등 원격 브라우저에서 FE에 접속할 때는 backend를 `--host 0.0.0.0`으로 열고,
`ACTION_ROUTER_CORS_ORIGINS`에 `http://<tailscale-ip>:3000`을 추가한다.

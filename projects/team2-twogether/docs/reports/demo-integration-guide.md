# 통합 데모 테스트 가이드 (팀원용) — `main`

`main` 브랜치를 pull 받아 **백엔드(FastAPI) + 프론트엔드를 함께 띄워**
노드1~4 + 프론트의 end-to-end 흐름을 **실서버 응답**으로 직접 돌려보는 방법입니다.
(목 데이터가 아니라 실제 추천 파이프라인이 동작합니다.)

> 프론트만 목으로 보던 가이드는 `frontend/DEMO.md`. 이 문서는 **풀스택 실연동**용입니다.

---

## 0. 사전 준비

| 도구 | 버전 | 비고 |
|---|---|---|
| Python | 3.10+ (개발은 3.14에서 확인) | 백엔드 |
| Node.js | **20.19+ 또는 22** | Vite 8 요구. 20.17은 경고 뜨지만 동작은 함 |

별도 API 키 **불필요** — 검색은 기본 `bm25`(로컬)라 Upstage/Qdrant 키가 없어도 됩니다.

---

## 1. 브랜치 받기

```bash
cd ASM_TEAM2_AI_STUDY
git fetch origin
git checkout main
git pull origin main
```

---

## 2. 백엔드 띄우기 (터미널 1)

```bash
# 레포 루트에서
python -m venv .venv && source .venv/bin/activate   # 이미 있으면 activate만
pip install -r requirements.txt

uvicorn backend.app.main:app --port 8000 --reload
```

확인:
```bash
curl localhost:8000/health      # {"status":"ok"}
```

---

## 3. 프론트엔드 띄우기 (터미널 2)

### ★ 3-1. `frontend/.env` 직접 생성 (필수)
`.env`는 git에 올라가지 않습니다(gitignore). **실서버 연동을 위해 직접 만들어야 합니다.**

```bash
cd frontend
cat > .env <<'EOF'
VITE_USE_MOCK=false
VITE_API_BASE=http://localhost:8000
EOF
```
> 목 데이터로 보고 싶으면 `VITE_USE_MOCK=true` 로 두세요.

### 3-2. 실행
```bash
npm install
npm run dev          # http://localhost:5173
```

---

## 4. 브라우저 접속 → **http://localhost:5173**

### 테스트 시나리오

**① 정상 추천 (멘토 카드 3장)**
입력:
```
FastAPI로 추천 API를 만드는데 모델 서빙 구조와 Docker 배포가 어렵습니다. Kubernetes 운영도 고민이에요.
```
→ "분석된 약점" 배너 + 멘토 카드(서지훈/이채린/윤서연), 각 카드에 적합도·키워드·추천 이유·도움 영역.

**② 확인 질문 (입력 부족)**
입력: `앱이요`
→ "어떤 프로젝트를 만들고 있는지…" 질문 + 선택지 4개.

**③ 확인 질문 왕복 (세션)**
②에서 선택지 클릭 → "답변하고 계속"
→ 원본 입력과 병합되어 추천 카드로 진행 (서버가 session_id로 원본을 기억).

> 입력 화면의 **예시 칩**을 누르면 텍스트가 자동으로 채워집니다.

---

## 5. 종료
각 터미널에서 `Ctrl-C`. (또는 `pkill -f uvicorn`, `pkill -f vite`)

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 추천 결과가 안 오고 에러 | 백엔드(8000)가 안 떠 있음 → 터미널1 확인, `curl localhost:8000/health` |
| 결과가 항상 똑같은 목 데이터 | `frontend/.env` 의 `VITE_USE_MOCK` 이 `false` 인지 + 프론트 **재시작**(env는 기동 시 로드) |
| CORS 에러(콘솔) | 프론트를 5173/3000 외 포트로 띄움 → 5173 사용, 또는 백엔드 CORS 허용 origin에 추가 필요 |
| `Vite requires Node 20.19+` | 동작은 하나 권장 버전 아님 → Node 22 권장(`nvm use 22`) |
| 8000 포트 점유 | 다른 포트로 띄우고 `.env`의 `VITE_API_BASE`도 같이 변경 |

## 알려진 이슈 (고도화 과제, 데모 영향 없음)
- **로딩 화면(S-02)이 거의 안 보임**: 실서버 응답이 빨라(~10ms) 로딩 연출이 스킵됨.
  기능은 정상. 추후 최소 로딩 시간 적용 예정 (3단계 보고서 참고).

---

## 무엇을 보는 데모인가 (검증 포인트)
- 노드1(입력 파싱·충분성) → 노드2(검색) → 노드3(적합도) → 노드4(카드)까지 **한 번의 요청으로 관통**.
- 입력 부족 시 **확인 질문 분기**, 답변 후 **세션 병합 재요청**.
- 프론트 ↔ FastAPI `/recommend` **실연동**(목 아님).

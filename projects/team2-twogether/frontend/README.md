# SWM 멘토 매칭 — 프론트엔드

내 프로젝트의 기술 스택·진행 단계·고민을 입력하면, **지금 가장 도움받아야 할 멘토를 추천 근거와 함께** 제시하는 서비스의 프론트엔드입니다. (LangGraph 기반 Agentic RAG 서비스의 클라이언트)

> 설계 문서: [`AGENT.md`](./AGENT.md) (엔지니어링 규약·API 계약), [`Design.md`](./Design.md) (디자인 시스템), [`docs_wireframe.html`](./docs_wireframe.html) (화면 명세 S-01~S-06)

## 기술 스택

React 19 · Vite · TypeScript · CSS Modules + CSS 변수. 라우터 없이 **단일 `viewState` 상태 머신**으로 화면을 전환하고, **단일 `POST /recommend`** 엔드포인트만 호출합니다.

## 실행

```bash
nvm use            # Node 22 (.nvmrc)
npm install
npm run dev        # 개발 서버 (기본 mock 모드)
npm run build      # 타입체크 + 프로덕션 빌드
npm run lint       # eslint
```

> **Node 22 이상** 필요(`.nvmrc` 참고). 백엔드(FastAPI) 없이도 mock으로 전체 흐름이 동작합니다.

## Mock 모드

백엔드 완성 전까지 `.env`의 `VITE_USE_MOCK=true`(기본값)로 mock 응답을 사용합니다.
실서버 연동 시 `VITE_USE_MOCK=false` + `VITE_API_BASE=http://localhost:8000`.

입력 텍스트의 키워드로 데모 시나리오가 분기됩니다(`src/mocks/recommend.ts`):

| 입력 예시 키워드 | 결과 |
|---|---|
| 배포 · 서빙 · MLOps | `recommended` — 멘토 카드 |
| 구조 · 아키텍처 · 기획 | `need_clarification` → 답변 후 `recommended` |
| WebRTC · 실시간 · 영상 | `limited` — 재검색 후 제한적 추천 배너 |
| `asdf` 등 의미 없는 입력 | 빈 결과(EMPTY) |
| `강제에러` 포함 | 에러(ERROR) |

S-01 화면의 예시 칩(배포 고민 / 구조 리뷰 / 실시간 영상)을 누르면 각 시나리오 문장이 채워집니다.

## 화면 흐름

```
INPUT(S-01) → LOADING(S-02) ─┬─ need_clarification → CLARIFY(S-03) → LOADING → …
                             ├─ recommended/limited → RESULT(S-04) → MentorDetailModal(S-05)
                             └─ mentors 0 / 오류 → EMPTY / ERROR(S-06)
```

재검색(low_confidence)은 화면 전환 없이 로딩 화면의 `refining` 안내로만 표현합니다.

## 디렉터리

```
src/
├─ App.tsx                  # viewState 머신
├─ types/api.ts             # /recommend 요청·응답 타입 (단일 진실 소스)
├─ hooks/useRecommend.ts    # 유일한 API 통신 지점 (직접 fetch 금지)
├─ mocks/recommend.ts       # mock 응답 + 데모 라우팅
├─ styles/                  # tokens.css · global.css
├─ components/common/       # Button · Chip · Banner (공용)
├─ components/input/        # StepProgress · ClarifyQuestion (FE-A)
├─ components/result/       # MentorCard · MentorDetailModal · StateView (FE-B)
└─ screens/                 # Input · Loading · Clarify · Result
```

## 작업 분담

- **FE-A** (입력·흐름): S-01/02/03, `viewState` 머신, 공용 types/mocks/hook
- **FE-B** (결과·멘토): S-04/05/06, 디자인 토큰·공통 컴포넌트·멘토 카드

## 가드레일 (AGENT.md §7)

추천 이유(`reason`)·약점(`gaps`)·`notice`는 백엔드 텍스트를 **그대로 표시만** 합니다(환각 방지).
"멘토링 신청·연락" 버튼은 두지 않습니다(MVP 외부 실행 제외). 확인 질문은 항상 1개.

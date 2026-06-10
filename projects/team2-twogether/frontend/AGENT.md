# AGENT.md — SWM 멘토 매칭 에이전트 (프론트엔드)

> 이 파일은 **두 프론트엔드 개발자와 각자의 AI 에이전트가 공유하는 단일 컨텍스트**입니다.
> 코드를 생성/수정하기 전에 에이전트는 항상 이 문서를 먼저 읽습니다.
> UI 스타일·컴포넌트 규칙은 `Design.md`를 함께 참조하세요.

---

## 0. 프로젝트 한 줄 정의

> 내 프로젝트의 기술 스택·진행 단계·고민을 입력하면, **지금 가장 도움받아야 할 멘토를 추천 근거와 함께** 제시하는 LangGraph 기반 Agentic RAG 서비스.

프론트엔드의 책임은 단 하나: **사용자 입력을 받아 백엔드(`/recommend`)에 보내고, 응답 `status`에 따라 화면을 전환해 추천 결과를 보여주는 것.** 추천 로직·약점 분석·검색은 전부 백엔드(LangGraph)의 몫이다.

---

## 1. 기술 스택 (전제)

| 구분 | 선택 | 비고 |
|---|---|---|
| 언어 | TypeScript | `any` 지양, 응답 타입은 `src/types/api.ts`에 단일 정의 |
| 프레임워크 | React 19 + Vite | 라우터 없음(단일 페이지 상태 전환) |
| 상태 | React state + 단일 `viewState` 머신 | 전역 store 불필요(Context 1개로 충분) |
| 스타일 | CSS 변수 + CSS Modules | `Design.md`의 토큰을 `tokens.css`로 정의 |
| 통신 | `fetch` 래핑한 `useRecommend()` 훅 | **컴포넌트에서 직접 fetch 금지** |
| 테스트 | (선택) Vitest + Testing Library | MVP에서는 핵심 분기만 |

> 스택은 교체 가능하나 **바꿀 경우 이 표를 먼저 수정하고 둘이 합의**한다. 기획서의 Streamlit으로 회귀할 경우 화면 흐름(2장)은 그대로 유지되며 컴포넌트만 Streamlit 위젯으로 매핑한다.

---

## 2. 디렉터리 구조

```
src/
├─ App.tsx                 # viewState 머신 + 화면 라우팅
├─ types/
│   └─ api.ts              # /recommend 요청·응답 타입 (단일 진실 소스)
├─ hooks/
│   └─ useRecommend.ts     # 유일한 API 통신 지점 (FE-A/B 공용)
├─ mocks/
│   └─ recommend.ts        # status 3종 mock 응답 (백엔드 완성 전 개발용)
├─ styles/
│   └─ tokens.css          # 디자인 토큰 (Design.md 기준)
├─ components/
│   ├─ common/             # Button, Chip, Banner 등 (공용)
│   ├─ input/              # FE-A: ProjectInput, ClarifyQuestion, StepProgress
│   └─ result/             # FE-B: MentorCard, MentorDetailModal, StateView
└─ screens/
    ├─ InputScreen.tsx     # S-01  (FE-A)
    ├─ LoadingScreen.tsx   # S-02  (FE-A)
    ├─ ClarifyScreen.tsx   # S-03  (FE-A)
    └─ ResultScreen.tsx    # S-04 + S-05/S-06 분기 (FE-B)
```

소유권은 폴더로 가른다 → **`input/`은 FE-A, `result/`는 FE-B, `common/`·`hooks/`·`types/`·`styles/`는 공용**(수정 시 상대에게 공유).

---

## 3. 개발 명령어

```bash
npm install
npm run dev        # 로컬 개발 서버
npm run build      # 프로덕션 빌드
npm run lint       # eslint + 타입 체크
# 백엔드(FastAPI)는 docker-compose로 별도 기동. 미기동 시 mock 사용(아래 6장)
```

> 실제 명령어가 위와 다르면 이 표를 갱신한다. 에이전트는 추정하지 말고 이 표의 명령어만 사용한다.

---

## 4. 아키텍처 — 단일 `viewState` 상태 머신

화면 전환은 라우팅이 아니라 **하나의 `viewState`** 로 관리한다.

```
INPUT ──submit──▶ LOADING ──┬─ status:need_clarification ─▶ CLARIFY ──answer──▶ LOADING
                            ├─ status:recommended/limited ─▶ RESULT
                            └─ error / empty ──────────────▶ ERROR / EMPTY
```

- `LOADING` 중 백엔드가 내부적으로 재검색하면 화면 전환 없이 `refining=true` 플래그만 켠다(별도 화면 없음).
- 확인 질문(`CLARIFY`) 라운드는 **1회**로 가정한다. 2회째가 와도 답변 후 결과로 진행하도록 방어 처리.
- `viewState`와 응답 데이터는 `App.tsx`(또는 단일 Context)가 들고 있고, 화면 컴포넌트는 props로만 받는다.

화면 ID와 우선순위는 화면 명세서(`S-01`~`S-06`)와 1:1 대응한다.

---

## 5. API 계약 — `POST /recommend` (★ 단일 엔드포인트)

프론트는 이 엔드포인트 **하나만** 호출한다. 응답 `status` 하나로 모든 분기가 결정된다.
타입은 반드시 `src/types/api.ts`에 정의하고 양쪽이 import 한다.

### 요청

```ts
interface RecommendRequest {
  session_id: string;          // uuid. 신규 또는 확인질문 후 동일 세션
  project_text: string;        // 자유 텍스트 (필수)
  tech_stack?: string[];       // 선택
  stage?: string;              // 선택
  clarify_answer?: string | null; // 확인 질문 응답 시에만 값
}
```

### 응답 (status 3종)

```ts
type RecommendResponse =
  | { status: "need_clarification"; question: string; options?: string[] }
  | { status: "recommended"; gaps: string[]; refined: boolean; mentors: Mentor[] }
  | { status: "limited"; gaps: string[]; mentors: Mentor[]; notice: string };

interface Mentor {
  name: string;
  domain: string[];
  keywords: string[];
  score: number;               // 적합도 0~100
  reason: string;              // 추천 이유 (백엔드 생성, 그대로 표시)
  can_help: string[];
  less_relevant_for: string[];
  profile_summary: string;
}
```

### 프론트 분기 규칙

| 조건 | 화면 |
|---|---|
| `status === "need_clarification"` | `CLARIFY` (S-03) |
| `status === "recommended"` 또는 `"limited"` | `RESULT` (S-04) — `limited`면 안내 배너 |
| `mentors.length === 0` | `EMPTY` (S-06) |
| HTTP/네트워크 오류 | `ERROR` (S-06) |

> **백엔드 합의 필요(1주차 초 확정):** ① 단계 진행 스트리밍 여부(S-02 방식) ② `session_id` 발급 주체 ③ `limited`를 별도 status로 줄지 `recommended + notice`로 줄지. — 확정되면 이 문서를 갱신.

---

## 6. Mock 우선 개발 (★ 병렬 작업의 핵심)

백엔드가 완성되기 전에도 화면을 실데이터처럼 개발하기 위해 **mock을 먼저 만든다.**

1. `src/mocks/recommend.ts`에 위 3종 status의 응답 샘플 JSON을 정의한다.
2. `useRecommend()`는 환경 플래그(`VITE_USE_MOCK`)로 mock/실서버를 전환한다.
3. FE-A는 `need_clarification` mock으로, FE-B는 `recommended`/`limited`/빈배열 mock으로 각자 화면을 완성한다.

> 에이전트에게 시킬 때: **"먼저 `types/api.ts`와 `mocks/recommend.ts`, `useRecommend` 훅부터 만들어"** 라고 지시하면 이후 화면 작업이 안정된다.

---

## 7. 절대 규칙 / 가드레일 (위반 금지)

1. **추천 이유·약점 텍스트를 프론트에서 생성·가공하지 않는다.** 백엔드가 준 `reason`/`gaps`/`notice`를 **그대로 표시**만 한다. (기획서의 환각 방지 원칙 — 멘토 프로필에 없는 경력/성과를 만들어내면 안 됨.)
2. **MVP 범위 밖 화면·기능을 만들지 않는다.** 로그인/인증, 마이페이지, 추천 이력, 멀티유저, 멘토 실제 연락·신청·일정 조율·매칭 확정 → **모두 제외.** "멘토링 신청" 버튼을 임의로 추가하지 말 것.
3. **확인 질문은 항상 1개.** 여러 질문을 한 번에 노출하지 않는다(기획서 톤앤매너).
4. **컴포넌트에서 직접 `fetch` 금지.** 모든 통신은 `useRecommend()`를 통한다.
5. **응답 타입은 `types/api.ts` 한 곳에서만 정의.** 화면마다 인라인 타입을 새로 만들지 않는다.
6. **상대 소유 폴더(`input/` ↔ `result/`)를 임의 수정하지 않는다.** 공용 폴더 수정 시 커밋 메시지에 명시하고 공유.
7. **시크릿·API 키를 코드/리포에 넣지 않는다.** Upstage 등 키는 백엔드에만 존재하며 프론트는 키를 다루지 않는다.

---

## 8. 화면별 완료 기준 (Definition of Done)

| 화면 | 완료 기준 |
|---|---|
| S-01 입력 | 빈 입력 시 버튼 비활성 / 제출 시 LOADING 전환 / 중복 제출 차단 |
| S-02 진행 | 4단계 라벨 표시 / `refining` 시 재검색 안내 / 타임아웃·에러 처리 |
| S-03 확인질문 | 질문 1개 + (옵션/자유입력) / 답변 병합해 동일 session 재요청 |
| S-04 결과 | 약점 요약 + 멘토 카드 2~3개 / `limited` 배너 / 카드→상세 오픈 |
| S-05 상세 | 프로필 전 필드 표시 / ESC·배경·✕ 닫기 / 포커스 트랩 |
| S-06 상태 | 빈/에러 공통 `StateView` / 재시도 버튼 동작 |

각 화면은 **데모 시나리오 3종(배포 멘토 / 구조 리뷰 확인질문 / WebRTC 재검색)** 에서 끝까지 동작해야 한다.

---

## 9. 커밋 / 브랜치 / 협업 규칙

- 브랜치: `feat/s01-input`, `feat/s04-result` 처럼 **화면 ID 기준**.
- 커밋: `feat(s04): 멘토 카드 적합도 배지 추가` 형식(타입 + 화면 + 요약).
- 공용 파일(`types/`, `hooks/`, `tokens.css`) 변경 PR은 **반드시 상대 리뷰** 후 머지.
- 매일 시작 시 `types/api.ts`가 최신인지 먼저 확인(계약이 바뀌면 모든 화면이 영향).

---

## 10. 에이전트에게 일을 시킬 때 (프롬프트 가이드)

- **단위로 쪼개서 위임한다.** "S-04 전체"보다 "`MentorCard` 컴포넌트 하나"가 결과가 안정적이다.
- 프롬프트에 **이 문서의 해당 섹션 + 화면 명세서의 해당 화면 표 + `Design.md` 토큰**을 컨텍스트로 붙인다.
- 항상 **mock과 타입을 먼저** 시키고, 화면은 그 위에 올린다.
- 에이전트가 7장 가드레일을 어기는 코드(예: 프론트에서 추천문구 생성, 신청 버튼 추가)를 내면 즉시 거부하고 규칙을 다시 지시한다.
- 결과는 **DoD(8장)와 대조**해서 받는다.
```

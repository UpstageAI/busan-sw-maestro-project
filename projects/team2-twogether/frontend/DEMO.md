# 프론트엔드 데모 테스트 가이드 (팀원용)

`feat/frontend-mvp` 브랜치를 pull 받아 **백엔드 없이** 프론트엔드 전체 흐름을 직접 돌려보는 방법입니다.
멘토 매칭 화면 6종(S-01~S-06)과 두 분기(확인 질문 / 재검색)가 **mock 데이터**로 end-to-end 동작합니다.

---

## 0. 사전 준비 — Node 22 (★ 중요)

이 프로젝트는 **Node 20.19 이상**이 필요합니다(Vite 8 요구사항). 권장은 **Node 22**.

```bash
node -v   # v20.19 미만이면 아래로 업그레이드
```

**nvm 사용 시** (프로젝트에 `.nvmrc`가 있어 버전이 자동 지정됨):

```bash
nvm install 22
nvm use            # frontend 폴더에서 실행하면 .nvmrc(22)를 읽음
```

> nvm이 없다면: macOS `brew install node@22`, 또는 https://nodejs.org 에서 22 LTS 설치.

---

## 1. 브랜치 받기

이미 레포를 clone 한 경우:

```bash
cd ASM_TEAM2_AI_STUDY
git fetch origin
git checkout feat/frontend-mvp
git pull origin feat/frontend-mvp
```

처음 받는 경우:

```bash
git clone https://github.com/rutczzo/ASM_TEAM2_AI_STUDY.git
cd ASM_TEAM2_AI_STUDY
git checkout feat/frontend-mvp
```

---

## 2. 설치 & 실행

```bash
cd frontend
nvm use            # Node 22 (.nvmrc) — nvm 미사용이면 생략
npm install
npm run dev
```

터미널에 뜨는 주소로 접속합니다 (기본값):

```
➜  Local:   http://localhost:5173/
```

> 백엔드(FastAPI)가 없어도 됩니다. `.env`의 `VITE_USE_MOCK=true`(기본값)로 mock 응답을 사용합니다.

---

## 3. 데모 시나리오

입력창 아래 **예시 칩**을 누르면 시나리오 문장이 자동으로 채워집니다 → **[추천받기]** 클릭.

| 예시 칩 | 보게 되는 흐름 |
|---|---|
| **배포 고민** | 분석 진행(S-02) → 멘토 카드 2명(서지훈 92 · 장민서 85) → 카드 클릭 시 상세 모달(S-05) |
| **구조 리뷰** | 분석 진행 → **확인 질문 1개**(S-03) → 선택지(성능/확장성/배포/보안) 답변 → 추천 결과(S-04) |
| **실시간 영상** | 분석 진행 → **"다시 찾는 중…" 재검색 표시** → **⚠ 제한적 추천 배너**(limited) + 점수 주황 톤 |

직접 타이핑해서 테스트할 수도 있습니다(키워드로 분기됨):

| 입력 키워드 | 결과 |
|---|---|
| 배포 · 서빙 · MLOps · 운영 | `recommended` 추천 카드 |
| 구조 · 아키텍처 · 기획 · 확신 | `need_clarification` 확인 질문 |
| WebRTC · 실시간 · 영상 · 스트리밍 | `limited` 제한적 추천 |
| `asdf`, `qwer` 등 의미 없는 입력 | 빈 결과(EMPTY) 화면 |
| 문장에 `강제에러` 포함 | 에러(ERROR) 화면 + [다시 시도] |

---

## 4. 같이 눌러볼 디테일 (체크포인트)

- **멘토 상세 모달**: 카드 클릭 → ✓ 도움 줄 수 있는 상황 / △ 덜 맞는 영역 / 추천 이유 표시.
  닫기는 **✕ · 배경 클릭 · ESC** 모두 동작, 닫으면 원래 카드로 포커스 복귀.
- **반응형**: 브라우저 창을 좁히면(<768px) 모달이 **바텀시트**로 전환, 터치 타깃 확대.
- **다시 입력하기**: 결과 화면에서 누르면 새 세션으로 처음(S-01)부터.
- **접근성**: Tab 키만으로 전체 조작 가능(포커스 링), 모달 내부 포커스 트랩.
- **가드레일 확인**: "멘토링 신청/연락" 버튼은 **의도적으로 없음**(MVP 외부 실행 제외). 추천 이유 텍스트는 백엔드(현재 mock)가 준 문장을 그대로 노출만 합니다.

---

## 5. 품질 확인 (선택)

```bash
npm run build   # 타입체크 + 프로덕션 빌드
npm run lint    # eslint
```

둘 다 에러 없이 통과해야 합니다.

---

## 6. 자주 겪는 문제

| 증상 | 해결 |
|---|---|
| `crypto.randomUUID is not a function` / Vite 실행 실패 | **Node 버전이 낮음.** `node -v` 확인 후 Node 22로 (`nvm use`) |
| `Port 5173 is in use` | 이미 떠 있는 dev 서버 종료: `pkill -f vite` 후 재실행 |
| 화면이 안 바뀌고 계속 로딩 | mock은 약 2초 지연이 정상(분석 단계 연출). 그래도 멈추면 콘솔(F12) 확인 |
| 추천이 항상 똑같이 나옴 | 의도된 동작 — mock은 입력 키워드로 분기합니다(위 3번 표 참고) |

---

## 7. 구조 한눈에

```
frontend/src/
├─ App.tsx                  # 단일 viewState 상태 머신 (라우터 없음)
├─ types/api.ts             # /recommend 요청·응답 타입 (단일 진실 소스)
├─ hooks/useRecommend.ts    # 유일한 API 통신 지점 (mock/실서버 전환)
├─ mocks/recommend.ts       # mock 응답 + 데모 시나리오 라우팅
├─ components/common · input · result
└─ screens/  Input · Loading · Clarify · Result
```

더 자세한 규약은 [`AGENT.md`](./AGENT.md), 디자인은 [`Design.md`](./Design.md), 화면 명세는 [`docs_wireframe.html`](./docs_wireframe.html) 참고.

---

## 작업 분담

- **FE-A**(김세현): 입력·진행·확인질문 (S-01/02/03), viewState 머신, 공용 types/mocks/hook
- **FE-B**(김동학): 결과·멘토·상태 (S-04/05/06), 디자인 토큰·공통 컴포넌트·멘토 카드

피드백/버그는 각 화면 담당자에게 공유해 주세요. 🙌

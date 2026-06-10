# Design.md — SWM 멘토 매칭 에이전트 (디자인 시스템)

> 두 프론트엔드 개발자가 **같은 컴포넌트·토큰·상태 규칙**으로 UI를 만들기 위한 공유 문서입니다.
> 엔지니어링 규약·API 계약은 `AGENT.md`를 함께 보세요. 화면 단위 요구사항은 화면 명세서(S-01~S-06)를 참조합니다.

---

## 1. 디자인 원칙

서비스의 에이전트 성격(짧고 단정한 존댓말의 **조력자**)을 UI 전체에 일관되게 반영한다.

1. **결과 중심, 설명 최소.** 사용자가 긴 글을 읽지 않아도 판단할 수 있게 한다. 화면의 주인공은 항상 "멘토 카드"와 "추천 이유"다.
2. **한 번에 하나만 묻는다.** 확인 질문도, 액션도 한 화면에 하나의 주요 결정만 노출.
3. **AI가 일하는 과정을 보여준다.** 단순 스피너 대신 단계 진행을 드러내 신뢰와 데모 임팩트를 만든다.
4. **근거를 드러낸다.** 점수·도움 영역·추천 이유를 함께 보여 "왜 이 멘토인지"가 항상 보이게 한다.
5. **차분하고 신뢰감 있게.** 화려한 그라데이션·과한 모션 지양. 종이 질감의 차분한 베이스 + 명확한 강조색.

---

## 2. 디자인 토큰

`src/styles/tokens.css`에 아래를 정의하고 모든 컴포넌트가 변수만 참조한다. **하드코딩된 색·px 금지.**

### 2.1 색상

```css
:root{
  /* surface — 스카이블루 브랜드에 맞춘 시원한 블루-그레이 중성색 */
  --color-bg:        #F2F7FB;  /* 페이지 배경 (에어리한 쿨톤) */
  --color-surface:   #FFFFFF;  /* 카드·모달 */
  --color-surface-2: #F7FAFD;  /* 보조 면 */
  --color-line:      #DCE6EE;  /* 기본 경계 */
  --color-line-strong:#C4D3DF;

  /* text — 블루와 어울리는 쿨 차콜 */
  --color-ink:   #14252F;      /* 본문 */
  --color-muted: #5A6B78;      /* 보조 텍스트 */
  --color-faint: #98A8B4;      /* 비활성·placeholder */

  /* brand — ★ 서비스 핵심 색상 #6BBBE9 (스카이블루) */
  --color-primary:      #6BBBE9; /* 시그니처: 강조·포커스·진행·선택 */
  --color-primary-deep: #237BAE; /* 흰 텍스트 올라가는 주 버튼·링크 (AA 대비 확보) */
  --color-primary-soft: #E2F1FB; /* 선택·소프트 배경 */

  /* semantic — 브랜드와 조화되는 계열 */
  --color-success:     #1F9E86; /* 적합도 높음 / 도움 영역 (인접한 틸그린) */
  --color-success-soft:#DEF1EC;
  --color-warn:        #D9824E; /* 제한적 추천 / 덜 맞는 영역 (블루의 보색 클레이) */
  --color-warn-soft:   #FBEADF;
}
```

> **핵심 색상 운용 원칙:** `#6BBBE9`는 밝아서 흰 텍스트 대비가 부족하다. 따라서 시그니처(`--color-primary`)는 **강조·포커스 링·진행 표시(◐)·선택된 칩·hover 하이라이트**에 쓰고, **흰 글자가 올라가는 면(주 버튼·링크)은 같은 계열의 딥 블루(`--color-primary-deep`)** 를 사용한다. 둘 다 같은 스카이블루 패밀리라 일관되게 보인다.

> 점수 색 규칙: `score ≥ 80` → success(틸그린), `60~79` → ink/muted, `< 60` 또는 `status:limited` → warn(클레이).

> 팔레트 한눈에: 스카이블루 `#6BBBE9` · 딥블루 `#237BAE` · 틸그린 `#1F9E86` · 클레이 `#D9824E` · 쿨차콜 `#14252F` · 배경 `#F2F7FB`. (블루 중심의 split-complementary 구성)

### 2.2 타이포그래피

```css
--font-sans: 'Pretendard', -apple-system, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, monospace;  /* 점수·태그·코드 */

--fs-display: 28px;  --lh-display: 1.2;   /* 화면 타이틀 */
--fs-title:   20px;  --lh-title:   1.3;   /* 섹션 제목 */
--fs-body:    15px;  --lh-body:    1.65;  /* 본문 */
--fs-sm:      13px;                       /* 보조 */
--fs-xs:      11px;                       /* 캡션·태그 */
--fw-regular:400; --fw-medium:500; --fw-semibold:600; --fw-bold:700;
```

한글 가독성을 위해 본문 `line-height`는 1.6 이상 유지. 멘토 추천 이유 등 읽기 텍스트는 `max-width: 60ch`.

### 2.3 간격 · 모양 · 그림자

```css
--space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px;
--space-5:24px; --space-6:32px; --space-8:48px;     /* 8px 그리드 */

--radius-sm:6px; --radius-md:10px; --radius-lg:14px; --radius-pill:999px;

--shadow-sm: 0 1px 2px rgba(27,26,23,.06);
--shadow-md: 0 6px 20px rgba(27,26,23,.10);   /* 카드 hover */
--shadow-lg: 0 16px 48px rgba(27,26,23,.18);  /* 모달 */

--z-modal: 1000; --z-toast: 1100;
```

---

## 3. 레이아웃 · 반응형

- 콘텐츠 최대 폭 `720px`, 중앙 정렬. 멘토 카드는 1열 세로 스택(2~3개뿐이라 그리드 불필요).
- 브레이크포인트: `≥ 768px` 데스크탑 / `< 768px` 모바일.
- 모바일: 좌우 패딩 `--space-4`, 모달은 **풀스크린 바텀 시트**로 전환.
- 버튼·입력은 모바일에서 최소 높이 `44px`(터치 타깃).

---

## 4. 컴포넌트 카탈로그

각 컴포넌트는 **anatomy(구성) → props → variants → states** 순으로 정의. 소유자(`AGENT.md` 폴더 규칙)를 표기.

### 4.1 `Button` · `common` · 공용

| variant | 용도 | 스타일 |
|---|---|---|
| `primary` | 추천받기, 답변하고 계속 | 배경 `--color-primary-deep`, 흰 텍스트 (AA 대비) · hover 시 살짝 밝게 |
| `ghost` | 처음으로, 다시 입력 | 투명 배경, `--color-line` 보더 |
| `text` | 부가 액션 | 텍스트만, hover 시 underline |

- sizes: `md`(기본 44px) / `sm`(36px).
- states: `default / hover(밝기↑·shadow-sm) / active / disabled(opacity .45, 커서 not-allowed) / loading(스피너 + 텍스트 잠금, 중복 제출 방지)`.

### 4.2 `Chip` / `Tag` · `common` · 공용

- 용도: 기술 스택, 도메인 태그(`domain[]`), 확인 질문 선택지, 예시 프롬프트.
- 모양: `--radius-pill`, `--fs-xs`, 보더 `--color-line`.
- variants: `default`(흰 배경) / `selected`(primary-soft 배경, **primary-deep 텍스트** · 1px primary 보더) / `interactive`(클릭 가능, hover 시 primary 보더 강조).
- 도메인 태그는 `--font-mono`로 표기해 키워드 느낌을 준다.

### 4.3 `MentorCard` · `result` · **FE-B**

추천 결과의 핵심. 클릭 시 `MentorDetailModal`을 연다.

**Anatomy**
```
┌─────────────────────────────────────┐
│ [아바타] 이름            적합도 92  │  ← 상단: 이름 + score 배지(우측)
│ #MLOps #Infra                       │  ← 도메인 태그(mono chip)
│ 추천 이유: 모델 서빙 약점과 직접… │  ← reason (2~3줄 클램프)
│ 도움 영역: 모델 배포 구조 설계 …  │  ← can_help 상위 1~2개
└─────────────────────────────────────┘
```

**Props**
```ts
interface MentorCardProps {
  mentor: Mentor;     // types/api.ts
  onOpen: (mentor: Mentor) => void;
}
```

**규칙**
- `reason`은 **백엔드 텍스트 그대로**. 프론트에서 요약·재작성 금지(환각 방지).
- score 배지 색: §2.1 점수 색 규칙을 따른다.
- `reason`은 `-webkit-line-clamp: 3`으로 자르고 전체는 상세 모달에서.
- states: `default / hover(shadow-md, 살짝 들림 translateY(-2px)) / focus(키보드 접근, outline)`.

### 4.4 `MentorDetailModal` · `result` · **FE-B**  (S-05)

**Anatomy**: 헤더(아바타·이름·도메인·✕) → `profile_summary` → ✓ `can_help[]`(success 톤) → △ `less_relevant_for[]`(warn 톤) → 이 프로젝트 추천 이유(`reason`).

**Props**
```ts
interface MentorDetailModalProps {
  mentor: Mentor | null;
  open: boolean;
  onClose: () => void;
}
```

**규칙**
- 추가 API 호출 없음(데이터는 결과 응답에 이미 포함).
- 닫기: ✕ / 배경(overlay) 클릭 / `ESC`. **포커스 트랩** 필수, 닫으면 카드로 포커스 복귀.
- 모바일은 바텀 시트. overlay 색 `rgba(27,26,23,.45)`, 그림자 `--shadow-lg`.
- "멘토링 신청/연락" **버튼 없음**(MVP 외부 실행 제외). 필요 시 비활성 안내 문구만.

### 4.5 `StepProgress` · `input` · **FE-A**  (S-02)

에이전트 파이프라인 단계 표시.

**단계(고정)**: `입력 분석 → 약점 분석 → 멘토 검색 → 적합도 평가`

**Props**
```ts
interface StepProgressProps {
  current: number;      // 진행 중 단계 index
  refining?: boolean;   // 재검색 중이면 하단 안내 표시
}
```

**상태 표기**: 완료 `✓`(success) / 진행 `◐`(primary, 펄스 애니메이션) / 대기 `○`(faint).
`refining`이면 리스트 아래에 한 줄: "검색 질의를 보정해 다시 찾는 중…" (warn 톤).

### 4.6 `ClarifyQuestion` · `input` · **FE-A**  (S-03)

**Anatomy**: 질문 텍스트(1개) → 선택지 chip(`options[]` 있을 때) + 자유 입력 textarea → `[답변하고 계속] / [처음으로]`.

**Props**
```ts
interface ClarifyQuestionProps {
  question: string;
  options?: string[];
  onSubmit: (answer: string) => void;
  onReset: () => void;
}
```

**규칙**
- 질문은 **항상 하나**만 노출.
- 선택지 클릭 또는 자유 입력 중 하나라도 채워지면 제출 활성.
- 제출 → 동일 `session_id` + `clarify_answer`로 재요청(`AGENT.md` 5장).

### 4.7 `StateView` · `result` · **FE-B**  (S-06)

빈/에러/타임아웃을 모두 처리하는 단일 컴포넌트.

**Props**
```ts
interface StateViewProps {
  type: "empty" | "error" | "timeout";
  message?: string;          // 없으면 type별 기본 문구
  action?: { label: string; onClick: () => void };
}
```

| type | 기본 문구 | 기본 액션 |
|---|---|---|
| `empty` | "적합한 멘토를 찾지 못했어요. 입력을 조금 더 구체화해볼까요?" | 다시 입력하기 |
| `error` | "잠시 문제가 생겼어요." | 다시 시도(마지막 요청 재전송) |
| `timeout` | "조금 더 걸리고 있어요…" | (대기 / 취소) |

아이콘 + 메시지 + 액션 버튼의 중앙 정렬 단순 구성.

### 4.8 `Banner` (제한적 추천) · `common` · 공용

- `status:limited`일 때 결과 상단에 노출. warn-soft 배경 + warn 좌측 보더 3px.
- 내용: 백엔드 `notice` 텍스트 그대로. 카드의 score 배지도 warn 톤으로 톤다운.

---

## 5. 상태 표현 규칙 (요약)

| 상태 | 시각 처리 |
|---|---|
| 로딩 | `StepProgress` 단계 진행. 스피너 단독 사용 지양 |
| 재검색 | 화면 전환 없이 `refining` 안내 한 줄 추가 |
| 제한적(limited) | `Banner` + score 배지 warn 톤 |
| 빈 결과 | `StateView type="empty"` |
| 에러 | `StateView type="error"` + 재시도 |

---

## 6. 모션 가이드

- 화면 전환: `opacity + translateY(8px)`, `200ms ease-out`. 과한 슬라이드/스케일 금지.
- 단계 진행 중(`◐`): 1.4s 펄스(opacity 0.5↔1).
- 카드 hover: `translateY(-2px)` + `shadow-md`, `150ms`.
- 모달: overlay fade `150ms`, 패널 `scale(.98→1)` `180ms`.
- 멘토 카드 등장: `stagger`로 60ms 간격 순차 등장(결과 화면 1회 연출).
- `prefers-reduced-motion`이면 모든 트랜지션 제거.

---

## 7. 접근성 체크리스트

- 모달: 포커스 트랩 / `ESC` 닫기 / `role="dialog"` `aria-modal` / 열릴 때 포커스 이동, 닫힐 때 복귀.
- 모든 인터랙티브 요소에 키보드 포커스 링(`:focus-visible`).
- 색만으로 의미 전달 금지: 적합도·도움/부적합 영역은 **색 + 아이콘/라벨** 병행(✓ / △).
- 버튼·칩에 충분한 대비(WCAG AA), 터치 타깃 44px.
- 단계 진행은 `aria-live="polite"`로 상태 변화 안내.
- 이미지/아바타에 `alt` 또는 장식이면 `aria-hidden`.

---

## 8. 보이스 & 마이크로카피

에이전트 톤: **짧고 단정한 존댓말, 조력자.** 장황한 설명 대신 다음 결정으로 안내한다.

| 위치 | 권장 카피 | 피할 것 |
|---|---|---|
| 입력 placeholder | "프로젝트 설명, 기술 스택, 진행 단계, 지금 고민을 편하게 적어주세요." | "여기에 입력하세요" |
| 추천받기 버튼 | "추천받기" | "AI 분석 시작하기!" |
| 로딩 | "에이전트가 프로젝트를 분석하고 있어요" | "잠시만 기다려 주세요…" |
| 확인 질문 | "추천을 위해 한 가지만 확인할게요" | 질문 여러 개 나열 |
| 제한적 추천 | (백엔드 `notice` 그대로) | 임의 변형·과장 |
| 빈 결과 | "입력을 조금 더 구체화해볼까요?" | "결과 없음" |

- **느낌표·이모지 남용 금지.** 차분한 신뢰감 유지.
- 사용자에게 결정을 떠넘기지 않되, 최종 선택(어떤 멘토에게 연락할지)은 사용자 몫임을 존중하는 문구를 쓴다.
```

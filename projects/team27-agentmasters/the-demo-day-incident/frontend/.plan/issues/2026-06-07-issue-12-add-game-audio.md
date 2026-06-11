# 2026-06-07 — 게임 분위기별 BGM과 상호작용 효과음 추가

- Date: 2026-06-07
- GitHub Issue: #12
- Status: Complete

## Goal

화면과 사건 분위기에 맞춰 자연스럽게 전환되는 BGM, 주요 상호작용을 구분하는 효과음, 지속되는 음소거 설정을 추가한다.

## Non-goals

- 외부 음원 파일 또는 유료 사운드 라이브러리 도입
- 기존 게임 진행 규칙과 API 계약 변경
- 모든 버튼에 개별 효과음 추가

## Context / Constraints

- 브라우저 자동재생 정책 때문에 첫 사용자 입력 전에는 오디오를 시작할 수 없다.
- 저작권 위험을 줄이기 위해 Web Audio API로 런타임에 직접 합성한다.
- 오디오 상태와 생성 로직을 대형 화면 컴포넌트에서 분리한다.

## Approach (Checklist)
- [x] **Step 0: Recon** (현재 화면 상태, 카드/대화/시스템 메시지 이벤트 확인)
- [x] **Step 1: Implementation** (`src/lib/audioDirector.ts`, 오디오 훅과 게임 이벤트 연결, 음소거 UI)
- [x] **Step 2: Tests** (`npm run lint`, `npx tsc --noEmit`, `npm run build`; 앱 내 브라우저 미지원으로 수동 청취 제외)
- [x] **Step 3: Rollout / Rollback** (추가 자산 없음, 오디오 모듈과 연결 제거로 롤백)

## Validation
- **Commands to run:** `npm run lint`, `npm run build`
- **Expected output:** ESLint 오류 없음, Next.js 프로덕션 빌드 성공

## Risks & Rollback
- **Risks:** 오디오 컨텍스트 누수, 전환 중 음량 급증, 사용자 입력 전 재생 시도, 모바일 UI 겹침
- **Rollback steps:** 오디오 훅 연결과 `audioDirector` 모듈을 제거하면 기존 동작으로 복귀

## Open Questions
- 없음. 절차적 합성을 기본 구현으로 선택한다.

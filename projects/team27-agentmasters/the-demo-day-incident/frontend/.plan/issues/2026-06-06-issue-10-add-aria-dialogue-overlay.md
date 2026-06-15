# 2026-06-06 — ARIA 대사 전체 화면 오버레이 추가

- Date: 2026-06-06
- GitHub Issue: #10
- Status: Implemented

## Goal

단서와 인물 최초 열람 시 `ariaScripts`를 전체 화면 암전 오버레이로 순차 재생하고, 서버 과열 경고 기록의 TRACE 응답에도 같은 연출을 사용한다.

## Non-goals

- 단서/인물 데이터 구조 변경
- 기존 해금 및 서버 상호작용 계약 변경
- 인트로와 엔딩 컷신 재설계

## Context / Constraints

- 기존 `interacted` 상태는 해금 진행에 사용되므로 오버레이 열람 여부와 분리한다.
- 상세 화면과 심문 화면을 먼저 열고 오버레이를 그 위에 표시해 기존 탐색 흐름을 유지한다.
- 새 게임에서는 오버레이 열람 기록을 초기화한다.

## Approach (Checklist)
- [x] **Step 0: Recon** (Inspect existing code, locate files)
- [x] **Step 1: Implementation** (`GamePrototype.tsx`에 공통 오버레이와 열람 상태 연결)
- [x] **Step 2: Tests** (`npm run lint`, `npm run build`)
- [x] **Step 3: Rollout / Rollback** (클라이언트 상태만 추가하며 별도 마이그레이션 없음)

## Validation
- **Commands to run:** `npm run lint`, `npm run build`
- **Expected output:** 오류 없이 통과하고 단서/인물 최초 진입 및 TRACE 클릭에서 오버레이가 표시된다.
- **Result:** lint/build 통과. 인앱 브라우저가 제공되지 않아 자동 UI 검증은 미실행.

## Risks & Rollback
- **Risks:** 비동기 TRACE 응답 중 상세 모달이 전환되거나, 오버레이가 기존 모달보다 낮은 레이어에 표시될 수 있다.
- **Rollback steps:** 관련 커밋을 되돌리면 기존 인라인 TRACE 메시지 및 상세 진입 흐름으로 복구된다.

## Open Questions
- 없음

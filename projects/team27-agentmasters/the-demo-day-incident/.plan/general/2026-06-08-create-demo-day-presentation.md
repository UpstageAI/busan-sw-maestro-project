# 2026-06-08 — 데모데이 발표 자료 제작

- Date: 2026-06-08
- GitHub Issue: None
- Status: Completed

## Goal

배포된 `The Demo Day Incident` 화면을 캡처하고, 실제 게임 테마를 반영한 3분 발표용 자료를 만든다.

## Non-goals

- 프론트엔드/백엔드 구현 변경
- 스토리 결말 또는 반전 공개
- 기술 스택 중심 발표로 구성

## Context / Constraints

- 발표는 아이디어와 차별점 중심이어야 한다.
- DB, LangGraph, 프론트 구현 세부는 청중 관심도가 낮으므로 최소화한다.
- 실제 배포 URL `https://frontend-plum-seven-77.vercel.app`의 어두운 모바일 게임 UI를 테마 기준으로 삼는다.
- 구현 상태는 issue 기준으로 보수적으로 말한다.

## Approach (Checklist)
- [x] **Step 0: Recon** (배포 화면 캡처, 흐름 확인)
- [x] **Step 1: Implementation** (HTML 발표 자료와 assets 생성)
- [x] **Step 2: Tests** (로컬 브라우저/정적 파일 확인)
- [x] **Step 3: Rollout / Rollback** (산출물 경로 안내, 필요 시 파일 삭제)

## Validation
- **Commands to run:**
  - `open` 또는 Chrome headless 캡처로 자료 렌더 확인
- **Expected output:**
  - 발표 자료 HTML이 열리고, 캡처 이미지가 깨지지 않는다.

## Risks & Rollback
- **Risks:**
  - 자동 캡처 진행 중 로컬 스토리지 상태가 달라 화면이 다르게 보일 수 있다.
  - 스포일러성 단서 화면을 발표 자료에 넣을 수 있다.
- **Rollback steps:** 생성한 발표 자료와 캡처 파일 삭제

## Open Questions
- None

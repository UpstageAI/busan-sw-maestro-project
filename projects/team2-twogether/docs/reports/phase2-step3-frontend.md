# Phase 2 · 3단계 완료 보고 — 프론트엔드 실서버 연동 (E2E)

> 담당: donghakk (통합 오너) · 브랜치: `feat/integration` · 병합 커밋: `c853686`

## 한 줄 요약
프론트 MVP(`feat/frontend-mvp`)를 `feat/integration`에 **병합**하고, 목 데이터 대신
**실 FastAPI 서버에 연결**해 입력→추천 흐름을 end-to-end로 검증했습니다.

## 변경 사항
- `git merge feat/frontend-mvp` → 프론트 전체(`frontend/`)가 통합 브랜치에 합류.
  **충돌 없음**(순수 additive, 백엔드 파일 무변경).
- 코드 수정은 없음 — 프론트가 이미 연동 친화적으로 설계돼 있었습니다:
  - `frontend/src/hooks/useRecommend.ts`가 **유일한 API 통신 지점**이고 이미
    `POST ${VITE_API_BASE}/recommend`를 구현(`VITE_USE_MOCK`으로 목/실서버 토글).
- 연결은 **환경변수 2개**로 끝납니다 (`frontend/.env`, gitignore 대상이라 로컬 설정):
  ```
  VITE_USE_MOCK=false
  VITE_API_BASE=http://localhost:8000
  ```

## 실행 방법 (팀원 재현용)
**터미널 1 — 백엔드**
```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --port 8000 --reload
```
**터미널 2 — 프론트**
```bash
cd frontend
# .env 에 VITE_USE_MOCK=false / VITE_API_BASE=http://localhost:8000 설정
npm install
npm run dev          # http://localhost:5173
```
브라우저에서 5173 접속 → 프로젝트 설명 입력 → 추천 카드 확인.
(목으로 되돌리려면 `.env`의 `VITE_USE_MOCK=true`)

## 검증
- **프론트 프로덕션 빌드 통과**(`npm run build`, `tsc -b`) → api.ts 계약과 **타입 정합 확인**.
- **CORS preflight(OPTIONS) 통과** — `access-control-allow-origin: http://localhost:5173`.
- **실 cross-origin POST** (Origin 헤더 포함) → `recommended` + 멘토 3명 정상 반환.
- 백엔드 전체 테스트 90개 통과 유지.

> 참고: 위는 HTTP 레벨(빌드+CORS+실응답) 검증입니다. 브라우저 UI 렌더링 최종 확인은
> 프론트 담당이 `npm run dev`로 한 번 더 눈으로 봐주시면 좋습니다.

## ⚠️ 알아두실 점
- **Node 버전**: 현재 로컬 Node 20.17 — Vite가 20.19+ 권장 경고를 냅니다. 빌드는 됐으나
  dev 서버 안정성을 위해 **Node 20.19+ 또는 22.12+ 권장**.
- `frontend/.env`는 gitignore 대상(로컬 전용). 커밋된 기본값(`.env.example`)은 `VITE_USE_MOCK=true`
  이므로, 각자 로컬에서 실연동 시 `.env`를 위처럼 설정하세요.
- limited/retry 상태는 1단계 보고서 참고 — 규칙 기반 모드에선 자연 도달하지 않습니다.

## 🔧 해결됨 — 로딩 화면(S-02) 가시화 (브랜치 `feat/web-ui-progress`)
**실서버 모드에서 로딩 화면(S-02, StepProgress)이 보이지 않던 이슈 해결.**
- 원인이었던 것: 로딩 연출 지연이 `useRecommend.ts`의 목 모드 분기에만 있었음. 실서버는
  응답이 ~10ms라 로딩 화면이 깜빡이고 바로 결과로 넘어가, 단계 애니메이션이 안 보였음.
- 적용한 해결: 실서버 분기에도 최소 로딩 시간 보장 —
  `await Promise.all([callServer(req), sleep(STEP_INTERVAL * STEP_COUNT)])`.
  서버 호출과 동시에 1.8초(단계 한 바퀴)를 돌려, 입력분석→약점분석→멘토검색→적합도평가
  4단계 진행이 사용자에게 또렷이 보인다. (Playwright로 로딩 중 단계 진행 캡처 검증)

## Phase 2 통합 현황
| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | LangGraph 그래프 조립 | ✅ `ebe0334` |
| 2 | FastAPI /recommend + 세션 | ✅ `448bc67` |
| 3 | 프론트 연동 (E2E) | ✅ `c853686` |

→ 노드1~4 + 프론트 **end-to-end 연결 완료.** 다음은 PR 통합 및 데모 마감.

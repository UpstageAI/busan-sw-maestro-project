# Phase 2 · 2단계 완료 보고 — FastAPI /recommend 서버 + 인메모리 세션

> 담당: donghakk (통합 오너) · 브랜치: `feat/integration` · 커밋: `448bc67`

## 한 줄 요약
1단계에서 만든 워크플로우 그래프를 **`POST /recommend` 하나로 노출**하는 FastAPI 서버를
구축했습니다. 확인 질문 왕복을 위한 **인메모리 세션**도 포함합니다.

## 변경 사항
| 파일 | 내용 |
|---|---|
| `backend/app/main.py` (신규) | FastAPI 앱, `POST /recommend`, `GET /health`, CORS, 인메모리 세션 |
| `backend/app/schemas/request.py` | `session_id` 필드 추가 (api.ts 계약 정합) |
| `requirements.txt` | `fastapi==0.136.3`, `uvicorn==0.49.0`, `httpx` 추가 |
| `tests/test_api.py` (신규) | TestClient 기반 테스트 5개 |

## 핵심 동작
- **`POST /recommend`**: 요청 → 그래프 state 변환 → `_GRAPH.invoke` → `final_response` 반환.
  응답은 프론트 계약(`status` 3종)과 1:1. 컴파일된 그래프는 1회만 생성해 재사용.
- **인메모리 세션 (`_SESSIONS`)**: 확인 질문(need_clarification) 왕복 동안 원본 입력
  (project_text/tech_stack/stage)을 `session_id`별로 기억 → 후속 요청이 `clarify_answer`만
  보내도 원본과 병합됩니다. 대화가 끝나면(추천/제한) 세션을 비웁니다.
  - 프로세스 재시작 시 휘발 — **데모/단일 인스턴스 전제** (영속화는 범위 밖).
- **CORS**: Vite(5173)·CRA(3000) dev origin 허용.

## ⚠️ 계약 변경 — FE/노드1 담당 확인 요망
`backend/app/schemas/request.py`의 `RecommendRequest`에 **`session_id: str = ""`를 추가**했습니다.
- 이유: 프론트 `api.ts`의 `RecommendRequest`는 `session_id`(uuid)를 보내는데 백엔드 스키마에
  없었습니다. 인메모리 세션의 키로도 필요.
- 영향: **추가(옵셔널) 필드라 기존 노드/입력 파서 로직에 영향 없음.** 프론트는 이미 전송 중.

## 검증
- **테스트 5개 신규 + 기존 85개 = 90개 전부 통과.**
- **실 HTTP(uvicorn) 스모크 확인**: `/health` OK, clarification/recommended 정상.
- 로컬 실행:
  ```bash
  pip install -r requirements.txt
  uvicorn backend.app.main:app --port 8000 --reload
  # 확인
  curl localhost:8000/health
  curl -X POST localhost:8000/recommend -H 'Content-Type: application/json' \
    -d '{"session_id":"demo","project_text":"FastAPI로 추천 API 만드는데 모델 서빙과 Docker 배포가 어렵습니다","tech_stack":["Python"]}'
  ```

## 응답 형태 (참고)
- `need_clarification`: `{status, question, options}`
- `recommended`: `{status, gaps, refined, mentors[]}`
- `limited`: `{status, gaps, mentors[], notice}`

## 다음 단계
→ 3단계: 프론트(`feat/frontend-mvp`)를 실서버에 연동.

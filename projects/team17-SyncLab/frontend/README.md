# ContextBridge Frontend

React + TypeScript + Vite 기반의 ContextBridge MVP 프론트엔드입니다.

## 실행

```bash
npm install
npm run dev
```

## 실제 API 연결

`.env`에 백엔드 주소를 넣으면 실제 `POST /api/analyze`를 호출합니다.

```bash
VITE_API_BASE_URL=https://your-backend.example.com
```

## MSW mock API

개발 모드에서 `VITE_API_BASE_URL`이 비어 있으면 MSW가 자동으로 켜지고,
브라우저에서 실제 `POST /api/analyze` 요청을 가로채 `api-docs.md` 형식의 응답을 반환합니다.

Mock 응답을 끄고 싶으면 `.env`에 아래처럼 설정합니다.

```bash
VITE_ENABLE_MSW=false
```

폼에 직접 입력한 뒤 “분석 시작”을 누르면 브라우저 네트워크 탭에서
`POST /api/analyze` 요청, `job_id` 응답, SSE 스트림 요청을 확인할 수 있습니다.

## SSE 분석 진행

분석 시작 시 `POST /api/analyze`로 `job_id`를 받은 뒤
`GET /api/analyze/{job_id}/stream`에 연결합니다.
`progress` 이벤트는 Agent Workflow 진행 화면에 반영하고,
`done` 이벤트의 `result`를 최종 보고서로 표시합니다.

개발 모드의 MSW도 같은 계약으로 `job_id`, 단계별 `progress`, 최종 `done` 이벤트를 반환합니다.

## 보고서 내보내기

분석 결과 화면의 `PDF 저장`은 브라우저 인쇄 기능을 사용해 보고서 영역만 PDF로 저장합니다.
`DOCX 다운로드`는 프론트엔드에서 `docx` 라이브러리로 Word 문서를 생성하므로 별도 백엔드 API가 필요하지 않습니다.

## 분석 이력 조회

화면 진입 시 `GET /api/analyses`로 완료된 분석 이력을 불러옵니다.
이력 카드를 선택하면 `GET /api/analyses/{id}`로 상세 결과를 조회해 기존 보고서 영역에 표시합니다.

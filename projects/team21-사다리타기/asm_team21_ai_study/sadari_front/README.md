# SOMA Busan Chatbot Frontend

SW마에스트로 부산 관련 질문을 입력하고 의도별 응답 흐름을 확인하는 챗봇형 MVP입니다.

## 구성

- `app/ui.py`: Streamlit 채팅 UI
- `Dockerfile`: 루트 FastAPI 백엔드와 Streamlit UI가 함께 사용할 이미지
- `docker-compose.yml`: 루트 `src.api.main:app` API와 UI 컨테이너 실행

## 실행

```bash
cp ../.env.example ../.env
# ../.env 에서 UPSTAGE_API_KEY 입력
docker compose up --build
```

- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs

## 현재 범위

현재 구현은 Streamlit UI가 루트 FastAPI 백엔드의 `/sessions`, `/chat/{session_id}` 계약에 바로 연결됩니다.
실제 RAG 답변을 위해서는 프로젝트 루트의 `.env`에 `UPSTAGE_API_KEY`를 설정하고 `data/chroma`에 문서 인덱스를 준비해야 합니다.

# Backend

## 시작 전 준비

`.env.example` 파일을 `.env`로 복사하고 API 키 입력

- `UPSTAGE_API_KEY` — [업스테이지 콘솔](https://console.upstage.ai)에서 발급
- `LANGSMITH_API_KEY` — [LangSmith](https://smith.langchain.com)에서 발급

## 실행

`backend` 폴더 터미널에서:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

`http://localhost:8000` 에서 확인

# 니가양보해

팀명: ListenUp  
팀 폴더: `team16-ListenUp`

## 프로젝트 소개

`니가양보해`는 단체 채팅에서 진행 중인 약속 논의를 분석해 시간, 장소, 메뉴 후보를 추천하는 약속 조율 서비스입니다.

사용자는 대화 내보내기 파일, 현재 약속 논의 구간, 참여자별 출발지와 조건을 입력합니다. 시스템은 현재 논의에서 언급된 후보와 제약 조건을 추출하고, 과거 약속에서 누가 더 많이 양보했는지 함께 고려해 공정한 약속 후보를 1~3순위로 제시합니다.

## 핵심 기능

- 카카오톡/단체 채팅 내보내기 파일 업로드
- 현재 약속 논의 구간 설정
- 참여자별 출발지와 시간, 장소, 메뉴, 예산 조건 입력
- 과거 대화 기반 참여자별 양보 이력 분석
- 현재 논의 기반 시간, 장소, 메뉴 후보 추출
- 과거 양보 이력과 현재 제약 조건을 반영한 후보 랭킹
- 1위 후보가 명확하면 단독 추천
- 상위 후보 점수 차이가 작으면 복수 선택지 제안
- 정보가 부족하면 추가 논의가 필요한 항목 안내
- 분석 흐름 추적을 위한 서버 로그 제공

## 기술 스택

Frontend

- Next.js 16
- React 19
- TypeScript
- TanStack Query
- Axios
- Tailwind CSS
- Zod

Backend

- Java 21
- Spring Boot 4
- Gradle
- RestClient

AI Server

- Python
- FastAPI
- LangGraph
- LangChain
- Upstage Solar API
- Pydantic

## 시스템 구조

```text
Frontend(:3000)
  -> Spring Backend(:8080)
  -> FastAPI/LangGraph AI Server(:8000)
  -> Upstage LLM
```

주요 역할은 다음과 같습니다.

- Frontend: 입력 폼, 파일 업로드, 분석 결과 화면
- Spring Backend: FE 요청 수신, multipart 요청 검증, AI 서버 프록시
- AI Server: 대화 파일 분석, LangGraph 워크플로우 실행, 최종 추천 생성

## LangGraph 워크플로우

```text
START
  -> history
  -> extract
  -> sufficiency route
      -> fallback
      -> rank
          -> route
              -> recommend
              -> negotiate
```

노드별 역할:

- `history`: 현재 논의 시작 이전 대화에서 참여자별 양보 이력 분석
- `extract`: 현재 논의 구간에서 후보 시간, 장소, 메뉴, 제약 조건 추출
- `sufficiency`: 추출 결과만으로 랭킹 가능한지 판단
- `rank`: 후보 조합을 점수화하고 1~3순위 정렬
- `recommend`: 1위 후보가 명확할 때 단독 추천 메시지 생성
- `negotiate`: 상위 후보 점수 차이가 작을 때 복수 선택지 제안
- `fallback`: 정보 부족 시 추가 논의 요청 메시지 생성

## 폴더 구조

```text
team16-ListenUp/
├── ai/
│   ├── app/
│   │   ├── agent/
│   │   ├── api/
│   │   └── schemas/
│   ├── main.py
│   └── requirements.txt
├── backend/
│   └── aisomabackend/
│       ├── src/
│       ├── build.gradle
│       └── gradlew
├── frontend/
│   ├── src/
│   ├── package.json
│   └── pnpm-lock.yaml
└── README.md
```

## 실행 방법

아래 순서대로 AI 서버, Spring 백엔드, 프론트엔드를 각각 다른 터미널에서 실행합니다.

### 1. AI 서버 실행

```bash
cd ai

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

`.env`에 Upstage API 키를 입력합니다.

```env
UPSTAGE_API_KEY=up-...
UPSTAGE_MODEL=solar-pro
```

서버 실행:

```bash
uvicorn main:app --reload --port 8000
```

헬스 체크:

```bash
curl http://localhost:8000/health
```

### 2. Spring 백엔드 실행

```bash
cd backend/aisomabackend
./gradlew bootRun
```

기본 포트는 `8080`입니다.

AI 서버 주소는 `src/main/resources/application.yml`에 설정되어 있습니다.

```yaml
ai:
  server:
    url: http://localhost:8000
```

### 3. 프론트엔드 실행

```bash
cd frontend
pnpm install
```

`.env.local`을 생성합니다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS=false
```

개발 서버 실행:

```bash
pnpm dev
```

브라우저에서 접속합니다.

```text
http://localhost:3000
```

주의: `NEXT_PUBLIC_API_BASE_URL`을 설정하지 않으면 프론트 로컬 mock API로 요청될 수 있습니다. 실제 AI 분석 흐름을 확인하려면 반드시 `http://localhost:8080`으로 설정해야 합니다.

## API

### Spring Backend

```text
POST /api/analyze
Content-Type: multipart/form-data
```

요청 필드:

- `conversationFile`: 대화 내보내기 파일
- `analysisRequest`: 분석 조건 JSON 문자열

`analysisRequest` 예시:

```json
{
  "targetDateText": "2026-06-07 일요일 저녁",
  "discussionStartedAt": "2026-06-02T18:50",
  "discussionEndedAt": "2026-06-04T20:23",
  "participants": [
    {
      "id": "p1",
      "name": "민수",
      "startLocation": "해운대",
      "conditionText": "해운대나 센텀 선호"
    }
  ]
}
```

### AI Server

```text
POST /api/analyze
Content-Type: multipart/form-data
```

Spring 백엔드가 동일한 multipart 형식으로 AI 서버에 요청을 전달합니다.

## 로그 확인

AI 서버는 요청별 `meetingId`를 기준으로 LangGraph 진행 상황을 출력합니다.

예시:

```text
[meetingId=...] [0/6 request] START
[meetingId=...] [1/6 history] START
[meetingId=...] [2/6 extract] DONE
[meetingId=...] [3/6 sufficiency] NEXT=rank
[meetingId=...] [4/6 rank] DONE - finalTop3=...
[meetingId=...] [5/6 route] NEXT=negotiate
[meetingId=...] [6/6 message] DONE
```

Spring 백엔드는 FE 요청 수신, AI 서버 요청 전송, 응답 상태코드, 처리 시간을 출력합니다.

## 검증 명령

AI 서버 문법 확인:

```bash
cd ai
PYTHONPYCACHEPREFIX=/tmp/asm-pycache .venv/bin/python -m py_compile app/api/analyze.py app/agent/nodes.py app/agent/prompts.py
```

프론트엔드 타입 체크:

```bash
cd frontend
pnpm typecheck
```

백엔드 컴파일:

```bash
cd backend/aisomabackend
./gradlew compileJava
```

## 제출 시 제외한 항목

다음 항목은 용량, 보안, 빌드 산출물 문제로 제출 폴더에 포함하지 않았습니다.

- `.git`
- `.idea`
- `node_modules`
- `.next`
- `.venv`
- `.gradle`
- `build`
- `target`
- `__pycache__`
- `ai/.env`

환경변수 예시는 `ai/.env.example`, `frontend/.env.example`에 포함되어 있습니다.

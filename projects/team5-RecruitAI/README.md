# 🐶 PathsDog - AI Hiring Match (자기소개서 기반 채용공고 추천 서비스)

![PathsDog AI](https://img.shields.io/badge/Status-Completed-success)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2+-6DB33F?logo=spring-boot&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-In_Memory_DB-DC382D?logo=redis&logoColor=white)
![Python](https://img.shields.io/badge/Python-AI_Agent-3776AB?logo=python&logoColor=white)

> **"자기소개서에서 바로 지원 우선순위를 뽑아냅니다."**
> 지원자의 자기소개서와 희망 조건을 바탕으로 최적의 채용 공고를 매칭하고, 합격을 위한 맞춤형 보완 포인트를 한 화면에서 제공하는 AI 맞춤형 채용 큐레이션 플랫폼입니다.

<br>

## 🎬 서비스 시연 및 주요 기능

### 1. 사용자 맞춤형 AI 공고 매칭
* **프로필 및 조건 입력:** 자기소개서 원문과 희망 직무(ex. 백엔드), 경력 수준, 희망 근무지, 기술 스택 등을 입력합니다.
* **상세 필터링:** '보상 정보가 있는 공고 우선', '마감 임박 공고 우선' 등 구직자의 실질적인 니즈를 반영한 필터링을 지원합니다.

### 2. 스마트 분석 리포트 제공
* **추천 공고 요약:** 전체 추천 공고 수, 평균 적합도, 1순위 추천 기업을 한눈에 대시보드 형태로 제공합니다.
* **In-depth 공고 분석:** 단순히 공고를 나열하는 것을 넘어, AI가 3가지 핵심 인사이트를 제공합니다.
  * **💡 추천 이유:** 내 자소서의 어떤 경험(ex. 대규모 트래픽 처리 경험)이 해당 공고와 매칭되는지 분석합니다.
  * **보완할 점:** 해당 포지션 지원 시 이력서에서 부족한 부분을 짚어줍니다.
  * **지원 전 점검 포인트:** 실제 지원하기 전 자소서에 반드시 추가하거나 다듬어야 할 방향성을 제시합니다.

### 3. 원클릭 공고 확인
* 매칭된 카드의 `공고 상세보기`를 통해 JD(Job Description) 원문을 즉시 확인하고, `원본 공고 보기` 버튼을 통해 실제 기업의 채용 페이지(ex. Toss Careers)로 다이렉트 이동합니다.

<br>

## 🏗 시스템 아키텍처 및 기술 스택

본 프로젝트는 프론트엔드, 백엔드(Spring Boot), AI(Python)가 결합된 **모노레포(Monorepo)** 구조로 개발되었습니다. 특히 AI의 무거운 텍스트 분석 처리 시간을 극복하기 위해 **Redis 기반의 비동기 폴링(Polling) 아키텍처**를 채택하여 사용자 경험(UX)을 극대화했습니다.

### 💻 기술 스택
* **Backend:** Java 21, Spring Boot 3.2, Spring Web, RestClient
* **In-Memory DB:** Redis (작업 상태 관리 및 결과 캐싱)
* **AI Server:** Python, LangGraph, PathsDog MCP 연동
* **Frontend:** React / Web UI

### ⚙️ 핵심 비즈니스 로직 (비동기 처리)
1. **Task 생성 (Client ➔ Backend):** 클라이언트가 자소서 데이터를 POST 요청하면, 백엔드는 즉시 UUID 기반의 `task_id`를 생성하여 반환합니다. (상태: `ACCEPTED`)
2. **비동기 위임 (Backend):** 메인 스레드는 응답을 반환하고 종료되며, 별도의 워커 스레드(`@Async`)가 AI 서버로 무거운 분석 요청을 전송합니다.
3. **상태 관리 (Redis):** 백엔드는 AI의 진행 상태(`PROCESSING`, `ERROR`, `COMPLETED`)를 Redis에 TTL(Time-To-Live)을 적용하여 임시 저장합니다.
4. **Polling (Client ➔ Backend):** 클라이언트는 발급받은 `task_id`로 일정 주기마다 GET 요청을 보내 상태를 확인하고, `COMPLETED` 상태가 되면 최종 분석 결과(JSON)를 받아 화면에 렌더링합니다.

<br>

## 📂 프로젝트 구조 (Monorepo)

```text
📦 pathsdog-ai-hiring-match
 ┣ 📂 frontend/               # 프론트엔드 웹 UI 코드
 ┣ 📂 backend/                # Spring Boot REST API 서버
 ┃ ┣ 📂 src/main/java/.../domain/jobs  # 핵심 도메인 (Async Worker, Service, DTO)
 ┃ ┗ 📂 src/main/java/.../global       # 공통 응답 포맷 (BaseResponse), CORS 설정
 ┗ 📂 ai/                     # Python 기반 AI 에이전트 및 MCP 연동 코드
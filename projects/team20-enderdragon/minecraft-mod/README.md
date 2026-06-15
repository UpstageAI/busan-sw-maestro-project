# Minecraft Coach (Fabric 모드)

마인크래프트 인게임에서 백엔드 코칭 에이전트(FastAPI)를 호출하는 **클라이언트 모드**.
웹뷰(Streamlit)가 검증용이라면, 이 모드가 기획서가 말한 **실제 메인 클라이언트**다 — 동일한 백엔드 API를 호출한다(채팅 명령은 `/chat/sync`, 코치 창은 토큰 스트리밍 `/chat`).

> 인게임 ↔ 백엔드 **연결 기반**(플러그인화, #13)에서 출발해 그 위에 코치 GUI(#15) · 인벤토리 인식(#18) · 할 일 HUD(#20) · 게임 상태 전송(#35) · 3×3 제작법 격자(#47) · 토큰 스트리밍(#53)을 쌓아 올렸다.

**스택**: Fabric · Minecraft 1.21.1 · Java 21 · Fabric API

---

## 사전 준비

- **JDK 21** (`java -version` → 21.x)
- 백엔드가 떠 있어야 함 — `project_code/`에서 `bash start.sh` → `http://localhost:8001`

## 빌드

```bash
cd minecraft-mod
./gradlew build          # 최초 1회는 마인크래프트/매핑 다운로드로 수 분 소요
# 산출물: build/libs/minecraft-coach-<버전>.jar
```

> Gradle은 동봉된 wrapper(`./gradlew`, 8.8)를 쓰므로 별도 설치가 필요 없다.

## 개발용 실행 (인게임 테스트)

```bash
./gradlew runClient      # 개발용 마인크래프트 클라이언트 실행
```

마인크래프트가 뜨면 → 싱글플레이 월드 입장 → 세 가지 진입점으로 코치를 쓸 수 있다.

**① 채팅 명령어** — 채팅에:

```
/coach 이제 뭐 해야 해?
/coach 철 곡괭이 만들고 싶은데 지금 돌 곡괭이밖에 없어
```

코치 응답이 채팅창에 출력된다. (`[코치] 물어보는 중…` → 답변)

**② 전용 GUI 화면** — 기본 키 **`K`** 를 누르면 코치 창이 열린다.

- 게임 채팅과 분리된 별도 창에서 대화 기록이 스크롤로 남는다.
- 아래 입력창에 메시지를 치고 **Enter** 또는 **보내기** 버튼으로 전송.
- 답변이 **토큰 단위로 흐르듯** 표시된다(SSE 스트리밍).
- 제작 질문이면 제목 아래에 **3×3 제작법 격자**가 아이콘으로 뜬다(슬롯 호버 시 이름 툴팁).
- 창을 닫았다 다시 열어도(K) 같은 세션 대화 기록이 유지된다.
- 키는 마크 **옵션 → 조작 → "마크 코치"** 에서 바꿀 수 있다.

**③ 할 일 목록 · HUD** — 코치 답변의 단계별 TODO가 자동으로 정리된다.

- 코치가 `- ` 불릿으로 안내한 단계를 파싱해 **화면 우측 상단 HUD**에 요약 표시한다.
- 기본 키 **`J`** 를 누르면 **할 일 목록 화면**이 열려 전체 항목을 보고 완료 처리할 수 있다.

> 세 진입점(`/coach` · K · J)은 모두 동일한 백엔드(`CoachApiClient`)를 호출하며, 호출 시 **현재 인벤토리와 게임 상태(시간·체력·좌표)를 자동으로 함께 전송**해 보유 아이템·상황에 맞는 답변을 받는다.

## 정식 설치 (선택)

`build/libs/`의 jar를 Fabric Loader가 설치된 마인크래프트 `mods/` 폴더에 넣는다.
**Fabric API**도 함께 `mods/`에 있어야 한다.

---

## 백엔드 주소 설정

기본값은 `http://localhost:8001`. 다른 주소(배포 서버 등)로 바꾸려면 둘 중 하나:

```bash
# 1) JVM 시스템 프로퍼티
./gradlew runClient -Dcoach.backend.url=http://192.168.0.10:8001

# 2) 환경변수
COACH_BACKEND_URL=http://192.168.0.10:8001 ./gradlew runClient
```

대화 맥락용 `thread_id`는 게임 실행마다 자동 생성(`mc-<uuid>`)되어, 한 실행 동안 후속 질문이 이어진다.

---

## 구조

```
src/main/java/com/enderdragon/coach/
  CoachClientMod.java        클라이언트 진입점 (명령어 + K·J 키 등록, HUD 등록)
  CoachCommand.java          /coach <메시지> 명령어 → 호출 → 채팅 출력
  api/
    CoachApiClient.java      chat()=sync 호출 · chatStream()=SSE 토큰 스트리밍 (java.net.http)
    ChatRequest.java         요청 DTO (message, thread_id, inventory, inventory_connected, game_state)
    ChatResponse.java        응답 DTO (answer, domain, sources, todos, recipe) + Recipe 격자
    StreamEvent.java         SSE 이벤트 DTO (event/node/data)
    InventorySnapshot.java   현재 인벤토리 캡처 → 요청에 포함
    GameStateSnapshot.java   시간·체력·배고픔·차원·좌표 캡처 → 요청에 포함
    CoachApiException.java    호출 실패 → 사용자 친화 메시지
  config/
    CoachConfig.java         백엔드 주소 · 세션 thread_id
  gui/
    CoachScreen.java         코치 GUI 화면 (대화기록·입력창·보내기, K로 열기, 토큰 스트리밍)
    RecipeGridWidget.java    3×3 제작법 격자 렌더링 (drawItem)
    CoachChatLog.java        세션 대화 로그 (열고 닫아도 유지)
    TodoList.java            코치 답변의 단계 파싱 → shortText(HUD)/fullText(목록)
    TodoHudRenderer.java     우측 상단 할 일 HUD 렌더링
    TodoScreen.java          할 일 목록 화면 (J로 열기, 완료 처리)
src/main/resources/
  fabric.mod.json            모드 메타데이터 (client 진입점)
  assets/minecraft_coach/lang/   키 이름 번역 (en_us, ko_kr)
```

### 백엔드 API 계약

| | |
| --- | --- |
| 엔드포인트 | `POST {backendUrl}/api/v1/chat/sync`(채팅 명령) · `POST .../chat`(코치 창, SSE) |
| 요청 | `{ "message": "...", "thread_id": "mc-...", "inventory": [{ "item": "minecraft:cobblestone", "count": 3 }], "inventory_connected": true, "game_state": { "time_of_day": "night", "health": 14, ... } }` |
| 응답 | `{ "answer": "...", "domain": "minecraft", "sources": [], "todos": [...], "recipe": { "output": "minecraft:iron_pickaxe", "count": 1, "grid": ["minecraft:iron_ingot", null, ...] } }` |

> `inventory`·`game_state`는 호출 시점의 플레이어 스냅샷이다. `recipe`는 제작 목표가 있을 때만 채워지며, `RecipeGridWidget`이 3×3 격자로 렌더링한다.

---

## 확장 포인트 (남은 작업)

- **웹뷰 레시피 표시**: 모드는 3×3 격자를 렌더하지만(`RecipeGridWidget`), 웹뷰용 ASCII 폴백은 미구현이다.
- **인게임 실검증**: 토큰 스트리밍·레시피 격자는 컴파일·와이어 포맷까지 확인했고, 실제 클라이언트 화면 검증이 남았다.
- **상태 확장**: 인벤토리·시간·체력·좌표는 자동 전송된다(`InventorySnapshot`·`GameStateSnapshot`). 주변 블록·몹 등 추가 상태를 더 실으면 정확도를 높일 수 있다.

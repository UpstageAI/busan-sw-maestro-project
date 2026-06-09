# 신규 기능 설계: 역질문 · 선택지 · 워크플로우 시각화

**날짜:** 2026-06-07  
**대상 브랜치:** feature/sungyoon

---

## 1. 목표

Streamlit 데모 UI에 3가지 기능을 추가한다.

1. **역질문** — 추천에 필요한 정보가 부족할 때 LLM이 질문 1개를 생성, 답변 후 재실행
2. **선택지 제공** — 단일 타임라인 대신 top-3 후보 카드 표시, 사용자가 선택 후 타임라인 생성
3. **워크플로우 시각화** — `app.stream()`으로 노드 완료 시마다 `st.status`에 체크 추가

---

## 2. 변경 파일

| 파일 | 변경 유형 |
|------|-----------|
| `src/agents/structure_a.py` | 노드 추가, 라우팅 변경, AgentState 확장 |
| `app/main.py` | 전체 UI 재작성 (스트리밍, 카드, 역질문) |

---

## 3. AgentState 확장

```python
needs_clarification: bool    # 정보 부족 여부 (기본 False)
clarification_question: str  # LLM 생성 역질문 (기본 "")
```

---

## 4. 그래프 구조 변경

### 4-1. 새 노드: `check_sufficiency`

`parse_intent` 완료 후 삽입. 기존 `parse_intent → classify_mode` 엣지를 교체한다.

```
parse_intent → route_after_intent (기존 유지)
    ├─ reject → compose_response → END   ← 기존 그대로
    └─ recommend → check_sufficiency     ← 신규 삽입
                      ├─ needs_clarification=True  → END
                      └─ needs_clarification=False → classify_mode → ... → END
```

**충분성 판정 규칙 (규칙 기반):**
- `mood_keywords` 비어 있고 `location_preference` 없으면 → 부족
- 그 외 → 충분

**역질문 생성 (LLM):**
- 부족 판정 시 Solar Pro로 자연스러운 한국어 질문 1개 생성
- 예: "어떤 분위기의 여행을 원하세요? 조용한 바다, 활기찬 도시, 산속 힐링 중에서 알려주시면 더 잘 맞는 곳을 추천해 드릴게요."
- 폴백: LLM 실패 시 고정 질문 "여행 분위기나 선호 지역을 조금 더 알려주시겠어요?"

### 4-2. 라우팅 함수 추가

```python
def route_after_sufficiency(state) -> str:
    return "clarify" if state.get("needs_clarification") else "recommend"
```

### 4-3. 프롬프트 추가 (`src/prompts/templates.py`)

`build_clarification_messages(intent_text: str) -> List[BaseMessage]`  
- 시스템: "사용자가 여행 추천을 요청했으나 정보가 부족합니다. 핵심 정보(분위기 또는 지역) 하나만 자연스럽게 되물어 주세요."
- 출력: 질문 문자열 1개 (JSON 아님, 평문)

---

## 5. Streamlit UI 재설계 (`app/main.py`)

### 5-1. session_state 키

| 키 | 역할 |
|----|------|
| `original_query` | 사용자 원본 쿼리 |
| `clarification_answer` | 역질문 답변 |
| `ranked` | 그래프 결과 top-3 |
| `intent` | 파싱된 TravelIntent |
| `selected_spot` | 사용자가 선택한 관광지 dict |
| `timeline_response` | 선택 후 생성된 타임라인 텍스트 |

### 5-2. 화면 흐름

```
① 쿼리 입력 + "추천 받기" 클릭
        ↓
② st.status 열림 → app.stream() 실행
   ✅ 의도 파싱
   ✅ 정보 충분성 확인
   ... (노드마다 체크 추가)
        ↓
③-A needs_clarification=True
   → 역질문 말풍선 표시
   → 답변 입력창 + "답변하기" 버튼
   → 클릭 시 "original_query + 답변" 합쳐 재실행 (② 부터)
        ↓
③-B needs_clarification=False
   → top-3 카드 3개 표시
   (name / region / mood 태그 / fitness_reason / "이 여행지로 보기" 버튼)
        ↓
④ 카드 선택
   → session_state.selected_spot 저장
   → compose_response 노드 함수 직접 호출 (그래프 재실행 없음)
   → 타임라인 텍스트 표시
```

### 5-3. 워크플로우 시각화

```python
NODE_LABELS = {
    "parse_intent":        "의도 파싱",
    "check_sufficiency":   "정보 충분성 확인",
    "classify_mode":       "참여자 분석",
    "generate_candidates": "후보 생성 (RAG)",
    "evaluate_fitness":    "적합도 평가",
    "filter_constraints":  "제약 필터링",
    "rank":                "최종 순위 선정",
    "compose_response":    "여행 일정 생성",
}
```

`app.stream(state, stream_mode="updates")` 사용.  
각 chunk: `{node_name: {state_updates}}` 형태.  
노드 완료마다 `st.write(f"✅ {label}")` 추가.

### 5-4. 카드 레이아웃

`st.columns(3)`으로 top-3 카드를 가로 배치.  
각 카드:
- 제목: `name`
- 부제: `region · type`
- 태그: `mood` 키워드 뱃지
- 설명: `fitness_reason` (1~2 문장)
- 버튼: `st.button("이 여행지로 보기", key=name)`

---

## 6. compose_response 단독 호출

카드 선택 후 타임라인 생성은 그래프를 재실행하지 않는다.  
`structure_a.compose_response` 함수를 직접 import해 호출한다.

```python
from src.agents.structure_a import compose_response

mini_state = {
    "intent": st.session_state.intent,
    "ranked": [selected_spot],  # 선택된 spot을 ranked[0]으로 취급
    "user_query": st.session_state.original_query,
}
result = compose_response(mini_state)
st.session_state.timeline_response = result.get("response", "")
```

---

## 7. 에러 처리

- 역질문 LLM 실패 → 고정 폴백 질문
- 스트리밍 중 예외 → `st.error()` 표시 후 session_state 초기화
- 카드 선택 후 compose_response 실패 → 폴백 (후보명 나열) 그대로 사용

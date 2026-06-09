"""Streamlit 로컬 데모 UI (구조 A) — LINE 스타일 디자인.

실행: streamlit run app/main.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from src.agents.structure_a import build_graph, compose_response

st.set_page_config(
    page_title="Travel AI · 여행지 추천",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── LINE 스타일 전체 CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

:root {
    --green:       #00B900;
    --green-dark:  #009900;
    --green-light: #E8F9E8;
    --green-mid:   #BBEABB;
    --bg:          #F5F6F8;
    --white:       #FFFFFF;
    --text:        #111111;
    --text-sub:    #777777;
    --text-muted:  #AAAAAA;
    --border:      #E4E4E4;
    --shadow-sm:   0 2px 10px rgba(0,0,0,0.06);
    --shadow-md:   0 6px 24px rgba(0,0,0,0.10);
    --radius:      20px;
    --radius-sm:   12px;
}

*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }

.stApp {
    font-family: 'Noto Sans KR', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

/* Streamlit 기본 UI 제거 */
header[data-testid="stHeader"],
footer, #MainMenu { display: none !important; }

.block-container {
    max-width: 820px !important;
    padding: 0 1.5rem 4rem !important;
    margin: 0 auto !important;
}

/* ── 앱 헤더 ─────────────────────────────────── */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 30px 0 26px;
    margin-bottom: 28px;
    border-bottom: 1.5px solid var(--border);
}
.app-header-icon {
    width: 50px; height: 50px;
    background: var(--green);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 14px rgba(0,185,0,0.30);
    flex-shrink: 0;
}
.app-header-copy { flex: 1; }
.app-header-copy h1 {
    margin: 0;
    font-size: 22px;
    font-weight: 900;
    color: var(--text);
    letter-spacing: -0.6px;
    line-height: 1;
}
.app-header-copy p {
    margin: 5px 0 0;
    font-size: 13px;
    color: var(--text-sub);
    font-weight: 400;
}
.app-header-pill {
    background: var(--green-light);
    color: var(--green-dark);
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 50px;
    border: 1px solid var(--green-mid);
    white-space: nowrap;
}

/* ── 검색 섹션 ───────────────────────────────── */
.search-card {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    box-shadow: var(--shadow-sm);
    margin-bottom: 24px;
}
.search-label {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.search-label span { color: var(--text-sub); font-weight: 400; font-size: 13px; }

/* 입력 필드 */
.stTextInput > label { display: none !important; }
.stTextInput > div > div > input {
    border: 2px solid var(--border) !important;
    border-radius: 50px !important;
    padding: 14px 22px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 15px !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--green) !important;
    background: var(--white) !important;
    box-shadow: 0 0 0 4px rgba(0,185,0,0.10) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-muted) !important;
}

/* 버튼 공통 */
.stButton > button {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 50px !important;
    padding: 12px 30px !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    letter-spacing: -0.2px !important;
}
/* Primary (추천 받기) */
.stButton > button[kind="primary"] {
    background: var(--green) !important;
    color: white !important;
    box-shadow: 0 3px 14px rgba(0,185,0,0.32) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--green-dark) !important;
    box-shadow: 0 6px 24px rgba(0,185,0,0.42) !important;
    transform: translateY(-2px) scale(1.02) !important;
}
/* Secondary (뒤로 가기 등) */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--green) !important;
    border: 2px solid var(--green) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--green-light) !important;
    transform: translateY(-1px) !important;
}
/* 카드 내 선택 버튼 */
.stButton > button:not([kind="primary"]):not([kind="secondary"]) {
    background: var(--green) !important;
    color: white !important;
    width: 100% !important;
    box-shadow: 0 2px 10px rgba(0,185,0,0.20) !important;
}
.stButton > button:not([kind="primary"]):not([kind="secondary"]):hover {
    background: var(--green-dark) !important;
    box-shadow: 0 5px 20px rgba(0,185,0,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── 워크플로우 상태 ─────────────────────��────── */
[data-testid="stStatus"] {
    background: var(--white) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stStatus"] summary {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}

/* ── 역질문 채팅 버블 ───────────────────────��─── */
.chat-wrap {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin: 20px 0 16px;
    animation: fadeSlideUp 0.35s ease forwards;
}
.chat-avatar {
    width: 42px; height: 42px;
    background: var(--green);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    box-shadow: 0 3px 10px rgba(0,185,0,0.25);
}
.chat-bubble {
    background: var(--green-light);
    border: 1.5px solid var(--green-mid);
    border-radius: 4px 18px 18px 18px;
    padding: 14px 18px;
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 15px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.65;
    max-width: 88%;
}

/* ── 섹션 헤더 ───────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 18px;
}
.section-dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    flex-shrink: 0;
}
.section-header h2 {
    font-size: 19px !important;
    font-weight: 900 !important;
    color: var(--text) !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}

/* ── 카드 (여행지) ──────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--white) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 24px !important;
    transition: all 0.25s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    border-color: var(--green-mid) !important;
    box-shadow: 0 8px 30px rgba(0,185,0,0.12) !important;
    transform: translateY(-3px) !important;
}

/* 순위 배지 */
.rank-badge {
    display: inline-flex;
    align-items: center; justify-content: center;
    width: 28px; height: 28px;
    background: var(--green);
    color: white;
    font-size: 14px;
    font-weight: 900;
    border-radius: 50%;
    margin-bottom: 12px;
    font-family: 'Noto Sans KR', sans-serif;
    box-shadow: 0 2px 8px rgba(0,185,0,0.30);
}
/* 무드 태그 */
.mood-wrap { margin: 10px 0; display: flex; flex-wrap: wrap; gap: 5px; }
.mood-tag {
    background: var(--green-light);
    color: var(--green-dark);
    font-size: 12px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 50px;
    font-family: 'Noto Sans KR', sans-serif;
    border: 1px solid var(--green-mid);
}
/* 지역·타입 메타 */
.spot-meta {
    font-size: 13px;
    color: var(--text-sub);
    font-family: 'Noto Sans KR', sans-serif;
    margin-bottom: 8px;
    font-weight: 500;
}
/* 피트니스 이유 */
.fitness-reason {
    font-size: 14px;
    color: var(--text-sub);
    font-family: 'Noto Sans KR', sans-serif;
    line-height: 1.6;
    margin-bottom: 16px;
}
/* 카드 이름 */
.spot-name {
    font-size: 18px;
    font-weight: 900;
    color: var(--text);
    font-family: 'Noto Sans KR', sans-serif;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}

/* ── 선택 여행지 헤더 ─────────────────────────── */
.selected-header {
    background: linear-gradient(135deg, var(--green-light) 0%, var(--white) 100%);
    border: 1.5px solid var(--green-mid);
    border-radius: var(--radius);
    padding: 22px 26px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    animation: fadeSlideUp 0.3s ease forwards;
}
.selected-icon { font-size: 28px; }
.selected-title {
    font-size: 19px;
    font-weight: 900;
    color: var(--text);
    font-family: 'Noto Sans KR', sans-serif;
    letter-spacing: -0.5px;
    margin: 0;
}
.selected-sub {
    font-size: 13px;
    color: var(--text-sub);
    font-family: 'Noto Sans KR', sans-serif;
    margin: 3px 0 0;
}

/* ── 타임라인 (네이티브 컴포넌트 스타일링) ──────── */
/* 타임라인 컨테이너 카드 */
.timeline-card [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 28px 32px !important;
}
/* 시간 컬럼 텍스트 */
.timeline-card [data-testid="column"]:first-child p {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: var(--green) !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}
/* 장소명 */
.timeline-card [data-testid="column"]:last-child strong {
    font-size: 15px !important;
    letter-spacing: -0.3px;
}
/* 활동 설명 */
.timeline-card [data-testid="column"]:last-child p {
    color: var(--text-sub) !important;
    font-size: 14px !important;
    line-height: 1.55 !important;
    margin: 2px 0 0 !important;
}
/* 구분선 */
.timeline-card hr {
    margin: 2px 0 !important;
    border-color: var(--bg) !important;
}
/* caption (이동수단·비용) */
.timeline-card [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 12px !important;
    margin-top: 5px !important;
}

/* ── 디버그 expander ─────────────────────────── */
[data-testid="stExpander"] {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--border) !important;
    background: var(--white) !important;
    overflow: hidden !important;
    margin-top: 32px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 13px !important;
    color: var(--text-muted) !important;
}

/* ── Spinner ─────────────────────────────────── */
.stSpinner > div { border-top-color: var(--green) !important; }

/* ── Alert ──────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── 애니메이션 ──────────────────────────────── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0);    }
}
</style>
""", unsafe_allow_html=True)

# ─── 노드 레이블 ───────────────────────────────────────────────────────────���
NODE_LABELS = {
    "parse_intent":       "의도 파싱",
    "check_sufficiency":  "정보 충분성 확인",
    "classify_mode":      "참여자 분석",
    "generate_and_score": "후보 선별 + 적합도 평가",
    "filter_constraints": "제약 필터링",
    "rank":               "최종 순위 선정",
    "compose_response":   "여행 일정 생성",
}

# ─── session_state 초기화 ────────────────────────────────────────────────────
_DEFAULTS = {
    "original_query": "",
    "ranked": [],
    "intent": None,
    "needs_clarification": False,
    "clarification_question": "",
    "selected_spot": None,
    "timeline_response": "",
    "timeline_object": None,
    "workflow_done": False,
    "run_error": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def reset_state() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v


def run_graph(query: str, allow_clarification: bool = True) -> None:
    app = build_graph()
    final_state: dict = {}
    with st.status("AI 분석 중...", expanded=True) as status:
        try:
            init = {"user_query": query, "allow_clarification": allow_clarification}
            for chunk in app.stream(init, stream_mode="updates"):
                for node_name, updates in chunk.items():
                    if node_name.startswith("__"):
                        continue
                    label = NODE_LABELS.get(node_name, node_name)
                    st.write(f"✅ {label}")
                    if isinstance(updates, dict):
                        final_state.update(updates)
            status.update(label="완료 ✅", state="complete")
        except Exception as e:
            status.update(label="오류 발생", state="error")
            st.session_state.run_error = str(e)
            return

    st.session_state.ranked = final_state.get("ranked", [])
    st.session_state.intent = final_state.get("intent")
    st.session_state.needs_clarification = final_state.get("needs_clarification", False)
    st.session_state.clarification_question = final_state.get("clarification_question", "")
    st.session_state.workflow_done = True


def show_timeline(timeline_obj, response_text: str) -> None:
    """Timeline 객체를 Streamlit 네이티브 컴포넌트로 렌더링한다."""
    st.markdown('<div class="timeline-card">', unsafe_allow_html=True)
    with st.container(border=True):
        if timeline_obj and getattr(timeline_obj, "items", None):
            st.markdown(f"**🗺️ {timeline_obj.destination} 추천 일정**")
            st.divider()
            items = timeline_obj.items
            for i, item in enumerate(items):
                col_time, col_content = st.columns([1.6, 4.4])
                with col_time:
                    st.markdown(f"**:green[{item.time}]**")
                with col_content:
                    st.markdown(f"**{item.place}**")
                    st.markdown(item.activity)
                    metas = []
                    if item.transport:
                        metas.append(f"🚗 {item.transport}")
                    if item.cost:
                        metas.append(f"💰 {item.cost}")
                    if metas:
                        st.caption("  ·  ".join(metas))
                if i < len(items) - 1:
                    st.divider()
        else:
            # 폴백: render_timeline 텍스트를 파싱해서 표시
            lines = [ln for ln in response_text.split("\n") if ln.strip()]
            if not lines:
                st.write("일정을 생성하지 못했습니다.")
            else:
                st.markdown(f"**{lines[0]}**")
                st.divider()
                for line in lines[1:]:
                    if "|" not in line:
                        continue
                    time_part, rest = line.split("|", 1)
                    sep = "—" if "—" in rest else "–"
                    if sep in rest:
                        place, activity = rest.split(sep, 1)
                    else:
                        place, activity = rest, ""
                    activity = activity.strip()
                    caption_text = ""
                    if "(" in activity:
                        activity, meta_raw = activity.split("(", 1)
                        caption_text = meta_raw.rstrip(")").strip()
                    col_t, col_c = st.columns([1.6, 4.4])
                    with col_t:
                        st.markdown(f"**:green[{time_part.strip()}]**")
                    with col_c:
                        st.markdown(f"**{place.strip()}**")
                        st.markdown(activity.strip())
                        if caption_text:
                            st.caption(caption_text)
                    st.divider()
    st.markdown('</div>', unsafe_allow_html=True)


# ─── 앱 헤더 ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-icon">✈️</div>
    <div class="app-header-copy">
        <h1>Travel AI</h1>
        <p>자연어로 원하는 여행을 말씀해 주세요</p>
    </div>
    <div class="app-header-pill">Solar Pro × LangGraph</div>
</div>
""", unsafe_allow_html=True)

# ─── 검색 카드 ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="search-card">
    <div class="search-label">🔍 어떤 여행을 원하세요? <span>목적지·기간·분위기를 자유롭게 입력하세요</span></div>
</div>
""", unsafe_allow_html=True)

# NOTE: st.markdown 으로 감싼 div 안에 Streamlit 위젯을 넣을 수 없어 바로 렌더링
query = st.text_input(
    "여행 검색",
    placeholder="예) 친구들이랑 1박 2일 활기찬 바다 여행 추천해줘",
    label_visibility="collapsed",
)

col_btn, col_space = st.columns([1, 3])
with col_btn:
    search_clicked = st.button("✈️ 추천 받기", type="primary", use_container_width=True)

if search_clicked and query.strip():
    reset_state()
    st.session_state.original_query = query
    run_graph(query)

# ─── 오류 ────────────────────────────────────────────────────────────────────
if st.session_state.run_error:
    st.error(f"워크플로우 오류: {st.session_state.run_error}")

# ─── 역질문 ──────────────────────────────────────────────────────────────────
if st.session_state.workflow_done and st.session_state.needs_clarification:
    q_text = st.session_state.clarification_question
    st.markdown(f"""
    <div class="chat-wrap">
        <div class="chat-avatar">🤖</div>
        <div class="chat-bubble">{q_text}</div>
    </div>
    """, unsafe_allow_html=True)

    clarification_answer = st.text_input("답변을 입력하세요", key="clarification_input")
    col_ans, _ = st.columns([1, 3])
    with col_ans:
        if st.button("💬 답변하기", type="primary", use_container_width=True) and clarification_answer.strip():
            combined = f"{st.session_state.original_query} {clarification_answer}"
            reset_state()
            st.session_state.original_query = combined
            run_graph(combined, allow_clarification=False)
            if st.session_state.workflow_done:
                st.rerun()

# ─── 추천 카드 ────────────────────────────────────────────────────────────────
elif st.session_state.workflow_done and st.session_state.ranked:

    if not st.session_state.selected_spot:
        st.markdown("""
        <div class="section-header">
            <div class="section-dot"></div>
            <h2>추천 여행지 TOP 3</h2>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(len(st.session_state.ranked))
        for i, (col, spot) in enumerate(zip(cols, st.session_state.ranked)):
            with col:
                with st.container(border=True):
                    moods = spot.get("mood", [])
                    mood_tags = "".join(f'<span class="mood-tag">{m}</span>' for m in moods)
                    reason = spot.get("fitness_reason", "")
                    st.markdown(f"""
                    <div class="rank-badge">{i + 1}</div>
                    <div class="spot-name">{spot.get('name', '')}</div>
                    <div class="spot-meta">{spot.get('region', '')} · {spot.get('type', '')}</div>
                    <div class="mood-wrap">{mood_tags}</div>
                    <div class="fitness-reason">{reason}</div>
                    """, unsafe_allow_html=True)
                    if st.button("이 여행지로 보기", key=f"select_{i}"):
                        st.session_state.selected_spot = spot
                        st.session_state.timeline_response = ""
                        st.session_state.timeline_object = None
                        st.rerun()

    # ─── 선택 후 타임라인 ─────────────────────────────────────────────────────
    if st.session_state.selected_spot:
        spot = st.session_state.selected_spot
        region_type = f"{spot.get('region', '')} · {spot.get('type', '')}"
        st.markdown(f"""
        <div class="selected-header">
            <div class="selected-icon">📍</div>
            <div>
                <p class="selected-title">{spot.get('name', '')}</p>
                <p class="selected-sub">{region_type}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.timeline_response:
            with st.spinner(f"{spot.get('name', '')} 일정 생성 중..."):
                mini_state = {
                    "intent": st.session_state.intent,
                    "ranked": [spot],
                    "user_query": st.session_state.original_query,
                }
                result = compose_response(mini_state)
                st.session_state.timeline_response = result.get(
                    "response", "일정을 생성하지 못했습니다."
                )
                st.session_state.timeline_object = result.get("timeline")

        st.markdown("""
        <div class="section-header">
            <div class="section-dot"></div>
            <h2>추천 일정</h2>
        </div>
        """, unsafe_allow_html=True)
        show_timeline(
            st.session_state.timeline_object,
            st.session_state.timeline_response,
        )

        col_back, _ = st.columns([1, 3])
        with col_back:
            if st.button("← 다른 여행지 보기", type="secondary", use_container_width=True):
                st.session_state.selected_spot = None
                st.session_state.timeline_response = ""
                st.session_state.timeline_object = None
                st.rerun()

# ─── 디버그 ──────────────────────────────────────────────────────────────────
if st.session_state.workflow_done:
    with st.expander("디버그: 추출된 의도 / 후보"):
        st.json({
            "intent": st.session_state.intent.model_dump()
            if st.session_state.intent else None,
            "needs_clarification": st.session_state.needs_clarification,
            "ranked": st.session_state.ranked,
        })

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components


API_URL = os.getenv("API_URL", "http://localhost:8000")

EXAMPLE_PROMPTS = [
    "합격자 제출 서류 목록 알려줘",
    "자유 멘토링 신청은 언제부터 가능해?",
    "멘토링 무단 불참하면 어떻게 돼?",
    "하이스퀘어 외부 개발 공간 운영 시간이 어때?",
    "Webex 어떻게 설치하고 활성화해?",
    "엑스퍼트 상담 월 몇 번 해야 해?",
    "연수생·멘토 소개 노션 링크 알려줘",
    "디자인씽킹 교육 내용 요약해줘",
]

CSS = """
<style>
/* ── Streamlit 기본 헤더/푸터 제거 ── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── 전체 ── */
.stApp { background: linear-gradient(160deg, #e8f4fd 0%, #dbeafe 100%); }

/* ── 사이드바 ── */
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #bfdbfe; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #1e3a5f !important; }
[data-testid="stSidebar"] hr { border-color: #bfdbfe !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #2563eb !important; font-size: 1.8rem !important; font-weight: 700 !important;
}
[data-testid="stSidebarUserContent"] .stButton button {
    background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af !important;
    border-radius: 10px; font-size: 0.82rem; text-align: left; transition: all 0.15s;
}
[data-testid="stSidebarUserContent"] .stButton button:hover {
    background: #2563eb; border-color: #2563eb; color: #ffffff !important;
}

/* ── 메인 ── */
.block-container {
    max-width: 800px; padding-top: 0 !important; padding-bottom: 5rem;
    padding-left: 1.5rem; padding-right: 1.5rem;
}

/* ── 상단 헤더 ── */
.chat-topbar {
    position: sticky; top: 0; z-index: 100;
    background: #ffffff; border-bottom: 1px solid #bfdbfe;
    padding: 0.9rem 1.2rem; margin: -1.5rem -1.5rem 1.5rem -1.5rem;
    display: flex; align-items: center; gap: 0.75rem;
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}
.chat-topbar-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #38bdf8);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
}
.chat-topbar-title { font-size: 1rem; font-weight: 700; color: #1e3a5f; line-height: 1.2; }
.chat-topbar-sub { font-size: 0.72rem; color: #60a5fa; }
.online-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; display: inline-block; margin-right: 4px; }

/* ── 웰컴 카드 ── */
.welcome-card {
    background: #ffffff; border-radius: 16px; padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(37,99,235,0.1); margin-bottom: 1.5rem;
    border: 1px solid #bfdbfe;
}
.welcome-card h3 { color: #1e3a5f; font-size: 1.1rem; margin: 0 0 0.5rem 0; }
.welcome-card p { color: #475569; font-size: 0.85rem; margin: 0 0 1rem 0; line-height: 1.6; }
.feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.feature-item {
    background: #eff6ff; border-radius: 10px; padding: 0.6rem 0.8rem;
    font-size: 0.8rem; color: #1e40af; display: flex; align-items: center; gap: 0.4rem;
}

/* ── 페이드인 애니메이션 ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.msg-row { animation: fadeInUp 0.2s ease; }

/* ── 말풍선 공통 ── */
.msg-row { display: flex; align-items: flex-end; gap: 0.5rem; margin-bottom: 0.75rem; }
.msg-row.user { flex-direction: row-reverse; }

.msg-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.msg-avatar.bot  { background: linear-gradient(135deg, #2563eb, #38bdf8); }
.msg-avatar.user { background: #e0f2fe; }

.msg-body { display: flex; flex-direction: column; max-width: 68%; gap: 0.2rem; }
.msg-row.user .msg-body { align-items: flex-end; }

.msg-name { font-size: 0.7rem; font-weight: 600; color: #3b82f6; margin-left: 0.15rem; }

.bubble {
    padding: 0.65rem 1rem; border-radius: 18px;
    font-size: 0.875rem; line-height: 1.6; word-break: break-word; white-space: pre-wrap;
}
.bubble.bot {
    background: #ffffff; color: #1e293b; border-top-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}
.bubble.user {
    background: linear-gradient(135deg, #2563eb, #3b82f6); color: #ffffff;
    border-top-right-radius: 4px; box-shadow: 0 2px 8px rgba(37,99,235,0.25);
}

/* ── 타임스탬프 ── */
.msg-time { font-size: 0.65rem; color: #94a3b8; margin: 0.1rem 0.2rem; align-self: flex-end; }

/* ── 복사 버튼 ── */
.bubble-actions { display: flex; align-items: center; gap: 0.4rem; margin-top: 0.2rem; }
.copy-btn {
    background: none; border: 1px solid #bfdbfe; border-radius: 6px;
    color: #93c5fd; font-size: 0.7rem; padding: 0.1rem 0.45rem; cursor: pointer;
    transition: all 0.15s; line-height: 1.4;
}
.copy-btn:hover { background: #eff6ff; color: #2563eb; border-color: #2563eb; }
.copy-btn:active { background: #dbeafe; }

/* ── 출처 카드 ── */
.source-wrap { margin-top: 0.4rem; display: flex; flex-direction: column; gap: 0.3rem; }
.source-card {
    background: #f0f9ff; border: 1px solid #bae6fd; border-left: 3px solid #38bdf8;
    border-radius: 0 10px 10px 0; padding: 0.45rem 0.75rem; font-size: 0.78rem; color: #0c4a6e;
}
.source-card b { display: block; color: #0369a1; margin-bottom: 0.1rem; }

/* ── 의도 뱃지 ── */
.intent-badge {
    display: inline-block; background: #dbeafe; color: #1d4ed8;
    font-size: 0.67rem; font-weight: 600; border-radius: 20px;
    padding: 0.1rem 0.55rem; margin-top: 0.3rem;
}

/* ── 타이핑 인디케이터 ── */
@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.35; }
    30%            { transform: translateY(-5px); opacity: 1; }
}
.typing-bubble {
    display: flex; align-items: center; gap: 5px;
    background: #ffffff; border-radius: 18px; border-top-left-radius: 4px;
    padding: 0.8rem 1.1rem; width: fit-content;
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}
.typing-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #93c5fd;
    animation: typing 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

/* ── 입력창 ── */
[data-testid="stChatInputContainer"] > div {
    background: #ffffff !important; border: 1.5px solid #93c5fd !important;
    border-radius: 26px !important; box-shadow: 0 2px 12px rgba(37,99,235,0.1) !important;
    padding: 0.2rem 0.5rem !important;
}
[data-testid="stChatInputContainer"] > div:focus-within {
    border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}
[data-testid="stChatInput"] textarea { color: #1e293b !important; font-size: 0.9rem !important; }
</style>
"""

def inject_js() -> None:
    components.html(
        """
        <script>
        (function() {
            const p = window.parent;

            p.fillChatInput = function(text) {
                const textarea = p.document.querySelector('[data-testid="stChatInput"] textarea');
                if (!textarea) return;
                const setter = Object.getOwnPropertyDescriptor(p.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(textarea, text);
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.focus();
            };

            p.document.addEventListener('click', function(e) {
                const copyBtn = e.target.closest('.copy-btn');
                if (copyBtn) {
                    const text = decodeURIComponent(copyBtn.getAttribute('data-text'));
                    p.navigator.clipboard.writeText(text).then(() => {
                        const prev = copyBtn.textContent;
                        copyBtn.textContent = '✓ 복사됨';
                        setTimeout(() => { copyBtn.textContent = prev; }, 1500);
                    }).catch(() => {});
                }
                const exBtn = e.target.closest('.ex-btn');
                if (exBtn) {
                    const prompt = exBtn.getAttribute('data-prompt');
                    if (prompt) p.fillChatInput(prompt);
                }
            });
        })();
        </script>
        """,
        height=0,
    )


def scroll_to_bottom() -> None:
    components.html(
        """
        <script>
        (function() {
            const main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
        })();
        </script>
        """,
        height=0,
    )


def init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "welcome"}]
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "waiting" not in st.session_state:
        st.session_state.waiting = False


def create_session() -> str:
    r = requests.post(f"{API_URL}/sessions", timeout=10)
    r.raise_for_status()
    return r.json()["session_id"]


def ensure_session() -> str:
    if not st.session_state.session_id:
        st.session_state.session_id = create_session()
    return st.session_state.session_id


def send_chat(session_id: str, message: str) -> requests.Response:
    return requests.post(f"{API_URL}/chat/{session_id}", json={"message": message}, timeout=30)


def post_chat(message: str) -> dict[str, Any]:
    sid = ensure_session()
    r = send_chat(sid, message)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        if r.status_code != 404:
            raise
        st.session_state.session_id = None
        r = send_chat(ensure_session(), message)
        r.raise_for_status()
    return r.json()


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _encode(text: str) -> str:
    import urllib.parse
    return urllib.parse.quote(text)


def render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>👋 안녕하세요! SOMA 부산 도우미입니다</h3>
            <p>SW마에스트로 부산 연수생을 위한 AI 어시스턴트예요.<br>
            OT 자료와 공지사항을 기반으로 질문에 즉시 답변해드려요.</p>
            <div class="feature-grid">
                <div class="feature-item">📋 제출 서류 안내</div>
                <div class="feature-item">📅 일정·심의 조회</div>
                <div class="feature-item">📝 멘토링 내용 요약</div>
                <div class="feature-item">🔗 관련 링크 추출</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message(message: dict[str, Any]) -> None:
    if message["role"] == "welcome":
        render_welcome()
        return

    role = message["role"]
    content = _escape(message["content"]).replace("\n", "<br>")
    sources = message.get("sources", [])
    intent = message.get("intent", "")
    ts = message.get("ts", "")

    if role == "user":
        st.markdown(
            f"""
            <div class="msg-row user">
                <div class="msg-body">
                    <div class="bubble user">{content}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.1rem">
                    <div class="msg-avatar user">🙋</div>
                    <span class="msg-time">{ts}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        source_html = ""
        if sources:
            cards = "".join(
                f'<div class="source-card"><b>📎 {_escape(s["source"])}</b>{_escape(s.get("preview", ""))}</div>'
                for s in sources
            )
            source_html = f'<div class="source-wrap">{cards}</div>'

        badge = f'<span class="intent-badge">#{_escape(intent)}</span>' if intent else ""
        raw_content = message["content"]
        encoded = _encode(raw_content)

        st.markdown(
            f"""
            <div class="msg-row">
                <div style="display:flex;flex-direction:column;align-items:center;gap:0.1rem">
                    <div class="msg-avatar bot">🤖</div>
                    <span class="msg-time">{ts}</span>
                </div>
                <div class="msg-body">
                    <span class="msg-name">SOMA 도우미</span>
                    <div class="bubble bot">{content}</div>{source_html}<div class="bubble-actions">
                        {badge}
                        <span class="copy-btn" data-text="{encoded}">📋 복사</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_typing() -> None:
    st.markdown(
        """
        <div class="msg-row">
            <div class="msg-avatar bot">🤖</div>
            <div class="msg-body">
                <span class="msg-name">SOMA 도우미</span>
                <div class="typing-bubble">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def submit_prompt(prompt: str) -> None:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "ts": datetime.now().strftime("%H:%M"),
    })
    st.session_state.waiting = True


def fetch_response(prompt: str) -> None:
    try:
        data = post_chat(prompt)
        st.session_state.messages.append({
            "role": "assistant",
            "content": data["answer"],
            "intent": data["intent"],
            "sources": data.get("sources", []),
            "ts": datetime.now().strftime("%H:%M"),
        })
    except requests.RequestException:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "API 서버에 연결할 수 없어요. 🔌\nFastAPI 컨테이너가 실행 중인지 확인해 주세요.",
            "intent": "연결 오류",
            "sources": [],
            "ts": datetime.now().strftime("%H:%M"),
        })
    st.session_state.waiting = False


# ── 앱 시작 ────────────────────────────────────────────────────
st.set_page_config(page_title="SOMA 부산 채팅", page_icon="💬", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)
inject_js()
init_state()

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💬 SOMA 부산")
    st.caption("SW마에스트로 부산 AI 도우미")
    st.divider()
    turn_count = sum(1 for m in st.session_state.messages if m.get("role") == "user")
    st.metric("대화 턴", turn_count)
    st.caption(f"API: {API_URL}")
    st.divider()
    st.markdown("**예시 질문**")
    btn_html = "".join(
        f'<span class="ex-btn" data-prompt="{_escape(p)}">{p}</span>'
        for p in EXAMPLE_PROMPTS
    )
    st.markdown(
        f"""
        <style>
        .ex-btn {{
            display: block; width: 100%; margin-bottom: 6px;
            background: #eff6ff; border: 1px solid #bfdbfe;
            color: #1e40af; border-radius: 10px; font-size: 0.82rem;
            text-align: left; padding: 0.45rem 0.75rem; cursor: pointer;
            transition: all 0.15s; font-family: inherit;
        }}
        .ex-btn:hover {{ background: #2563eb; border-color: #2563eb; color: #fff; }}
        </style>
        {btn_html}
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── 헤더 ───────────────────────────────────────────────────────
st.markdown(
    """
    <div class="chat-topbar">
        <div class="chat-topbar-avatar">🤖</div>
        <div>
            <div class="chat-topbar-title">SOMA 부산 도우미</div>
            <div class="chat-topbar-sub">
                <span class="online-dot"></span>SW마에스트로 부산 AI 어시스턴트
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 메시지 목록 ────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_message(msg)

# ── 타이핑 인디케이터 or 응답 fetch ────────────────────────────
if st.session_state.waiting:
    render_typing()
    last_user = next(
        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
        None,
    )
    if last_user:
        fetch_response(last_user)
        st.rerun()
    else:
        st.session_state.waiting = False

# ── 자동 스크롤 ────────────────────────────────────────────────
scroll_to_bottom()

# ── 입력 ──────────────────────────────────────────────────────
prompt = st.chat_input("메시지를 입력하세요...")
st.caption("↵ Enter로 전송")

pending = st.session_state.pending_prompt
if pending:
    st.session_state.pending_prompt = None
    submit_prompt(pending)
    st.rerun()

if prompt:
    submit_prompt(prompt)
    st.rerun()

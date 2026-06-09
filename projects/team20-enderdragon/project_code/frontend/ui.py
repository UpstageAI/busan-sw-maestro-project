import os
import json
from uuid import uuid4

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
STREAM_ENDPOINT = f"{BACKEND_URL}/api/v1/chat"

st.set_page_config(page_title="마인크래프트 초보 가이드", page_icon="🧱", layout="wide")
st.title("🧱 마인크래프트 초보 가이드")
st.caption("막막할 때, 지금 내 상황에서 '다음 한 걸음'을 물어보세요. (예: \"방금 시작했는데 뭐부터 해야 해?\")")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 메시지 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 참고한 위키 문서"):
                for src in msg["sources"]:
                    st.caption(f"• {src}")

NODE_STATUS = {
    "analyze": "🔍 질문 분석 중...",
    "clarify": "🤔 상황 파악 중...",
    "retrieve": "📚 위키 검색 중...",
    "respond": "✍️ 답변 생성 중...",
    "ask":     "💬 되묻기 준비 중...",
}

if prompt := st.chat_input("마인크래프트에 대해 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_area = st.empty()
        answer_area = st.empty()
        full_answer = ""
        sources: list[str] = []

        try:
            with httpx.stream(
                "POST",
                STREAM_ENDPOINT,
                json={"message": prompt, "thread_id": st.session_state.thread_id},
                timeout=120.0,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        payload = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    event_type = payload.get("event", "")

                    if event_type == "node":
                        node = payload.get("node", "")
                        if node in NODE_STATUS:
                            status_area.caption(NODE_STATUS[node])
                        # 되묻기 노드 → 질문을 바로 표시 (토큰 없음)
                        if node == "ask":
                            try:
                                node_data = json.loads(payload.get("data", "{}"))
                                full_answer = node_data.get("final_answer", "")
                                if full_answer:
                                    answer_area.markdown(full_answer)
                            except (json.JSONDecodeError, AttributeError):
                                pass

                    elif event_type == "token":
                        full_answer += payload.get("data", "")
                        answer_area.markdown(full_answer + "▌")  # 커서 효과

                    elif event_type == "done":
                        status_area.empty()
                        try:
                            done_data = json.loads(payload.get("data", "{}"))
                            sources = done_data.get("sources", [])
                            # 토큰이 없었던 경우(되묻기 등) done에서 최종 답변 보장
                            if not full_answer:
                                full_answer = done_data.get("answer", "")
                        except json.JSONDecodeError:
                            pass
                        if full_answer:
                            answer_area.markdown(full_answer)
                        break

        except Exception as e:
            status_area.empty()
            full_answer = f"오류: {e}"
            answer_area.markdown(full_answer)

        if sources:
            with st.expander("📚 참고한 위키 문서"):
                for src in sources:
                    st.caption(f"• {src}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_answer,
        "sources": sources,
    })

with st.sidebar:
    st.subheader("💬 대화 목록")

    if st.button("➕ 새 대화", use_container_width=True):
        st.session_state.thread_id = str(uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()

    try:
        resp = httpx.get(f"{BACKEND_URL}/api/v1/sessions", timeout=5.0)
        sessions = resp.json()
        for sess in sessions:
            tid = sess["thread_id"]
            preview = sess["preview"]
            label = (preview[:22] + "…") if len(preview) > 22 else preview
            is_current = tid == st.session_state.thread_id
            btn_label = f"▶ {label}" if is_current else label

            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(btn_label, key=f"sess_{tid}", use_container_width=True):
                    if tid != st.session_state.thread_id:
                        msgs_resp = httpx.get(
                            f"{BACKEND_URL}/api/v1/sessions/{tid}/messages",
                            timeout=5.0,
                        )
                        st.session_state.thread_id = tid
                        st.session_state.messages = [
                            {"role": m["role"], "content": m["content"], "sources": []}
                            for m in msgs_resp.json()
                        ]
                        st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{tid}"):
                    httpx.delete(
                        f"{BACKEND_URL}/api/v1/sessions/{tid}", timeout=5.0
                    )
                    if tid == st.session_state.thread_id:
                        st.session_state.thread_id = str(uuid4())
                        st.session_state.messages = []
                    st.rerun()
    except Exception:
        st.caption("목록을 불러올 수 없습니다")

    st.divider()
    st.caption(f"세션: `{st.session_state.thread_id[:8]}…`")

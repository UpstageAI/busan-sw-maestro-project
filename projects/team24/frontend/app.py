import json
import os
import time
from html import escape
from textwrap import dedent

import streamlit as st
import httpx
import pandas as pd

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")
STEP_VISIBLE_DELAY_SECONDS = 1.0

PIPELINE_STEPS = [
    ("extract_text", "1. 텍스트 추출"),
    ("resolve_contract_type", "2. 계약 유형 결정"),
    ("split_clauses", "3. 조항 분리"),
    ("analyze_clauses", "4. 조항별 위험 여부 분석"),
    ("has_risky_clause", "5. 위험 조항 존재 여부 확인"),
    ("classify_risk", "6-A. 위험도 분류"),
    ("summarize", "7-A. 위험 조항 요약"),
    ("build_safe_result", "6-B. 안전 기본 요약 생성"),
    ("finalize", "8. 결과 반환"),
]

STEP_DESCRIPTIONS = {
    "extract_text": "업로드한 파일에서 계약서 본문을 읽습니다.",
    "resolve_contract_type": "자동 감지 또는 사용자가 선택한 계약 유형을 확정합니다.",
    "split_clauses": "계약서 본문을 조항 단위로 나눕니다.",
    "analyze_clauses": "각 조항에 위험 요소가 있는지 분석합니다.",
    "has_risky_clause": "위험 조항이 있는지 확인해 다음 경로를 결정합니다.",
    "classify_risk": "위험 조항이 있을 때 high/medium/low로 분류합니다.",
    "summarize": "위험 조항이 있을 때 전체 위험 요약을 생성합니다.",
    "build_safe_result": "위험 조항이 없을 때 불필요한 분류와 LLM 요약을 생략합니다.",
    "finalize": "기존 API 응답 형식에 맞춰 결과를 반환합니다.",
}

RISK_PATH_STEPS = {"classify_risk", "summarize"}
SAFE_PATH_STEPS = {"build_safe_result"}

APP_CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(224, 231, 255, 0.8), transparent 34rem),
        linear-gradient(135deg, #fff7ed 0%, #f8fafc 42%, #eef2ff 100%);
}
.main .block-container {
    max-width: 920px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}
h1 {
    color: #2f2745;
    letter-spacing: -0.04em;
}
.cute-hero {
    border: 1px solid rgba(196, 181, 253, 0.45);
    border-radius: 1.4rem;
    padding: 1.15rem 1.25rem;
    margin: 0.8rem 0 1.2rem;
    background: rgba(255, 255, 255, 0.76);
    box-shadow: 0 1.2rem 3rem rgba(99, 102, 241, 0.12);
}
.cute-hero-title {
    color: #6d4aff;
    font-size: 1.02rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}
.cute-hero-text {
    color: #6b647d;
    font-size: 0.94rem;
}
.stButton > button {
    border: 0;
    border-radius: 999px;
    padding: 0.55rem 1.15rem;
    color: white;
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    box-shadow: 0 0.7rem 1.4rem rgba(139, 92, 246, 0.24);
    font-weight: 800;
}
.stButton > button:hover {
    color: white;
    border: 0;
    transform: translateY(-1px);
}
div[data-testid="stFileUploader"] section {
    border: 1px dashed rgba(139, 92, 246, 0.5);
    border-radius: 1rem;
    background: rgba(255, 255, 255, 0.78);
}
div[data-testid="stExpander"] {
    border: 1px solid rgba(196, 181, 253, 0.48);
    border-radius: 1rem;
    background: rgba(255, 255, 255, 0.7);
    box-shadow: 0 0.8rem 2rem rgba(99, 102, 241, 0.08);
}
.overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.65rem;
    margin-top: 0.55rem;
}
.overview-card {
    border: 1px solid rgba(221, 214, 254, 0.95);
    border-radius: 0.95rem;
    padding: 0.75rem 0.85rem;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(245, 243, 255, 0.85));
}
.overview-title {
    color: #5b3cc4;
    font-weight: 800;
    font-size: 0.92rem;
    margin-bottom: 0.2rem;
}
.overview-text {
    color: #6b647d;
    font-size: 0.82rem;
    line-height: 1.45;
}
</style>
"""

PROCESS_LOG_CSS = """
<style>
.pipeline-card {
    border: 1px solid rgba(221, 214, 254, 0.95);
    border-radius: 1rem;
    padding: 0.8rem 0.95rem;
    margin: 0.55rem 0;
    background: rgba(255, 255, 255, 0.86);
    box-shadow: 0 0.8rem 1.8rem rgba(99, 102, 241, 0.08);
}
.pipeline-title {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    font-weight: 700;
}
.pipeline-message {
    color: #746b89;
    font-size: 0.92rem;
    margin-top: 0.25rem;
}
.pipeline-badge {
    border-radius: 999px;
    padding: 0.13rem 0.55rem;
    font-size: 0.78rem;
    font-weight: 700;
    margin-left: auto;
}
.pipeline-pending { color: #94a3b8; }
.pipeline-running { color: #7c3aed; }
.pipeline-success { color: #059669; }
.pipeline-skipped { color: #d97706; }
.pipeline-failed { color: #dc2626; }
.pipeline-badge.pipeline-pending { background: #f1f5f9; }
.pipeline-badge.pipeline-running { background: #ede9fe; }
.pipeline-badge.pipeline-success { background: #d1fae5; }
.pipeline-badge.pipeline-skipped { background: #fef3c7; }
.pipeline-badge.pipeline-failed { background: #fee2e2; }
.pipeline-spinner {
    width: 0.9rem;
    height: 0.9rem;
    border: 0.16rem solid rgba(124, 58, 237, 0.18);
    border-top-color: #7c3aed;
    border-radius: 50%;
    display: inline-block;
    animation: pipeline-spin 0.8s linear infinite;
}
@keyframes pipeline-spin {
    to { transform: rotate(360deg); }
}
</style>
"""


def render_process_logs(logs: list[dict]) -> None:
    if not logs:
        return

    log_by_step = {
        log.get("step"): log
        for log in logs
        if isinstance(log, dict) and log.get("step")
    }
    executed_steps = set(log_by_step)
    skipped_steps = _get_skipped_steps(executed_steps)

    with st.expander("분석 프로세스 로그", expanded=True):
        st.caption("실행된 단계와 조건부 분기로 건너뛴 단계를 순서대로 보여줍니다.")
        for step, label in PIPELINE_STEPS:
            log = log_by_step.get(step)
            description = STEP_DESCRIPTIONS.get(step, "")
            if log:
                status = log.get("status", "info")
                message = log.get("message", "")
                body = f"**{label}**  \n{message}"
                if description:
                    body += f"  \n{description}"
                if status == "success":
                    st.success(body)
                elif status == "failed":
                    st.error(body)
                else:
                    st.info(body)
            elif step in skipped_steps:
                st.warning(f"**{label}**  \n조건부 분기로 실행하지 않았습니다.  \n{description}")
            else:
                st.info(f"**{label}**  \n아직 실행되지 않았거나 로그가 없습니다.  \n{description}")

        extra_logs = [
            log
            for log in logs
            if isinstance(log, dict) and log.get("step") not in dict(PIPELINE_STEPS)
        ]
        if extra_logs:
            st.markdown("**추가 로그**")
            for log in extra_logs:
                st.write(f"[{log.get('step', 'unknown')}] {log.get('message', '')}")


def render_process_overview() -> None:
    with st.expander("분석 프로세스 안내", expanded=False):
        st.caption("분석 시작 후 아래 단계들이 순서대로 진행됩니다.")
        cards = ["""<div class="overview-grid">"""]
        for step, label in PIPELINE_STEPS:
            description = STEP_DESCRIPTIONS.get(step, "")
            cards.append(
                dedent(
                    f"""
                    <div class="overview-card">
                        <div class="overview-title">{escape(label)}</div>
                        <div class="overview-text">{escape(description)}</div>
                    </div>
                    """
                )
            )
        cards.append("</div>")
        st.markdown("".join(cards), unsafe_allow_html=True)


def _get_skipped_steps(executed_steps: set[str]) -> set[str]:
    if not executed_steps:
        return set()
    if "build_safe_result" in executed_steps:
        return RISK_PATH_STEPS
    if executed_steps.intersection(RISK_PATH_STEPS):
        return SAFE_PATH_STEPS
    return set()


def build_initial_process_state() -> dict[str, dict]:
    return {
        step: {
            "label": label,
            "state": "pending",
            "message": STEP_DESCRIPTIONS.get(step, ""),
            "visible": step == PIPELINE_STEPS[0][0],
        }
        for step, label in PIPELINE_STEPS
    }


def render_live_process_logs(process_state: dict[str, dict], placeholder) -> None:
    html_parts = [PROCESS_LOG_CSS]
    for step, _ in PIPELINE_STEPS:
        item = process_state[step]
        if not item.get("visible"):
            continue
        state = item["state"]
        label = escape(item["label"])
        message = escape(item.get("message", ""))
        icon = _get_process_icon(state)
        badge = _get_process_badge(state)
        html_parts.append(
            dedent(
                f"""
            <div class="pipeline-card">
                <div class="pipeline-title pipeline-{state}">
                    {icon}
                    <span>{label}</span>
                    <span class="pipeline-badge pipeline-{state}">{badge}</span>
                </div>
                <div class="pipeline-message">{message}</div>
            </div>
            """
            )
        )

    placeholder.markdown("".join(html_parts), unsafe_allow_html=True)


def _get_process_icon(state: str) -> str:
    if state == "running":
        return '<span class="pipeline-spinner"></span>'
    if state == "success":
        return "<span>✓</span>"
    if state == "skipped":
        return "<span>-</span>"
    if state == "failed":
        return "<span>!</span>"
    return "<span>○</span>"


def _get_process_badge(state: str) -> str:
    return {
        "pending": "대기",
        "running": "처리 중",
        "success": "완료",
        "skipped": "생략",
        "failed": "실패",
    }.get(state, "대기")


def update_process_state(process_state: dict[str, dict], event: dict) -> None:
    step = event.get("step")
    if step not in process_state:
        return

    process_state[step]["visible"] = True
    event_name = event.get("event")
    if event_name == "step_started":
        process_state[step]["state"] = "running"
        process_state[step]["message"] = event.get("message", "처리 중입니다.")
    elif event_name == "step_finished":
        process_state[step]["state"] = (
            "failed" if event.get("status") == "failed" else "success"
        )
        process_state[step]["message"] = event.get("message", "")
    elif event_name == "step_skipped":
        process_state[step]["state"] = "skipped"
        process_state[step]["message"] = event.get("message", "조건부 분기로 생략했습니다.")
    elif event_name == "error":
        process_state[step]["state"] = "failed"
        process_state[step]["message"] = event.get("message", "오류가 발생했습니다.")


def analyze_with_stream(uploaded_file, selected_contract_type: str) -> dict | None:
    process_state = build_initial_process_state()
    process_placeholder = st.empty()
    render_live_process_logs(process_state, process_placeholder)

    try:
        with httpx.stream(
            "POST",
            f"{BACKEND_URL}/analyze/stream",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            },
            data={"contract_type": selected_contract_type},
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event.get("event") == "completed":
                    return event.get("result")
                update_process_state(process_state, event)
                render_live_process_logs(process_state, process_placeholder)
                if event.get("event") in {"step_started", "step_skipped"}:
                    time.sleep(STEP_VISIBLE_DELAY_SECONDS)
                if event.get("event") == "error":
                    st.error(f"분석 실패: {event.get('message')}")
                    return None
    except httpx.HTTPStatusError as e:
        message, process_logs = get_error_detail(e.response)
        st.error(f"분석 실패: {message}")
        render_process_logs(process_logs)
    except Exception as e:
        st.error(f"분석 실패: {e}")
    return None


def get_error_detail(response: httpx.Response) -> tuple[str, list[dict]]:
    fallback_message = f"백엔드 요청에 실패했습니다. (HTTP {response.status_code})"

    try:
        response.read()
    except httpx.ResponseNotRead:
        return fallback_message, []

    try:
        payload = response.json()
    except ValueError:
        return response.text or fallback_message, []

    if not isinstance(payload, dict):
        return str(payload) or fallback_message, []

    detail = payload.get("detail", {})
    if response.status_code == 404 and detail == "Not Found":
        return (
            "백엔드의 /analyze/stream 엔드포인트를 찾지 못했습니다. "
            "백엔드 서버를 최신 코드로 재시작해 주세요.",
            [],
        )

    if isinstance(detail, dict):
        return (
            detail.get("message", fallback_message),
            detail.get("process_logs", []),
        )
    return str(detail) or fallback_message, []


st.set_page_config(page_title="계약문서 위험조항 분석 Agent", page_icon="📄")
st.markdown(APP_CSS, unsafe_allow_html=True)

st.title("계약문서 위험조항 분석 Agent")
st.markdown(
    """
    <div class="cute-hero">
        <div class="cute-hero-title">계약서 속 위험 조항을 차근차근 살펴볼게요.</div>
        <div class="cute-hero-text">
            파일을 올리고 계약 유형을 고르면, 텍스트 추출부터 요약까지 진행 상황을 단계별로 보여줍니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("계약서 파일을 업로드하세요", type=["pdf", "docx", "txt"])

contract_type = st.selectbox(
    "계약 유형을 선택하세요",
    ["자동 감지", "근로", "전세", "외주", "이용약관", "기타"],
)

render_process_overview()

RISK_COLOR = {"high": "🔴", "medium": "🟡", "low": "🟢"}

live_process_rendered = False

if st.button("분석 시작"):
    if not uploaded_file:
        st.warning("파일을 먼저 업로드해주세요.")
    else:
        result = analyze_with_stream(uploaded_file, contract_type)
        if not result:
            st.stop()
        live_process_rendered = True
        st.session_state["result"] = result

if "result" in st.session_state:
    result = st.session_state["result"]

    if result.get("detected_type"):
        st.caption(f"자동 감지된 계약 유형: **{result['detected_type']}**")

    if not live_process_rendered:
        render_process_logs(result.get("process_logs", []))

    st.subheader("전체 요약")
    st.info(result.get("summary", "요약 결과가 없습니다."))

    clauses = [
        clause
        for clause in result.get("clauses", [])
        if isinstance(clause, dict)
    ]
    risky_clauses = [clause for clause in clauses if clause.get("is_risky") is True]

    st.subheader("조항별 분석 결과")
    if risky_clauses:
        rows = [
            {
                "위험도": (
                    RISK_COLOR.get(c.get("risk_level"), "")
                    + " "
                    + str(c.get("risk_level", "unknown")).upper()
                ),
                "조항 (앞 120자)": str(c.get("clause", ""))[:120]
                + ("..." if len(str(c.get("clause", ""))) > 120 else ""),
                "분석 이유": c.get("reason", "분석 이유가 없습니다."),
            }
            for c in risky_clauses
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.subheader("조항 상세 설명")
        for i, clause in enumerate(risky_clauses):
            risk_level = str(clause.get("risk_level", "unknown"))
            clause_text = str(clause.get("clause", ""))
            label = (
                f"{RISK_COLOR.get(risk_level, '')} "
                f"[{risk_level.upper()}] {clause_text[:60]}..."
            )
            with st.expander(label):
                st.markdown(f"**전체 조항**\n\n{clause_text}")
                if st.button("상세 설명 보기", key=f"explain_{i}"):
                    with st.spinner("설명 생성 중..."):
                        try:
                            resp = httpx.post(
                                f"{BACKEND_URL}/explain",
                                json={"clause": clause_text},
                                timeout=60,
                            )
                            resp.raise_for_status()
                            st.markdown(resp.json()["explanation"])
                        except Exception as e:
                            st.error(f"설명 실패: {e}")
    else:
        st.success("위험 조항이 발견되지 않았습니다.")

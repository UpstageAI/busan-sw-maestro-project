from __future__ import annotations

from typing import Callable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from services.analyzer import analyze_clauses, detect_contract_type
from services.classifier import classify_risk
from services.extractor import extract_text, split_clauses
from services.summarizer import get_no_risk_summary, summarize


class ProcessLog(TypedDict):
    step: str
    status: str
    message: str


class AnalysisState(TypedDict, total=False):
    file_bytes: bytes
    filename: str
    requested_contract_type: str
    text: str
    detected_type: str | None
    resolved_type: str
    clauses: list[str]
    analysis: list[dict]
    classified: list[dict]
    summary: str
    process_logs: list[ProcessLog]
    result: dict


class AnalysisPipelineError(RuntimeError):
    def __init__(
        self,
        step: str,
        message: str,
        process_logs: list[ProcessLog],
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.step = step
        self.process_logs = process_logs
        self.status_code = status_code


def _log(step: str, status: str, message: str) -> ProcessLog:
    return {"step": step, "status": status, "message": message}


def _run_node(
    state: AnalysisState,
    step: str,
    operation: Callable[[], dict],
    success_message: Callable[[dict], str],
) -> dict:
    logs = list(state.get("process_logs", []))
    try:
        updates = operation()
    except AnalysisPipelineError:
        raise
    except Exception as exc:
        message = str(exc).strip() or "알 수 없는 오류가 발생했습니다."
        logs.append(_log(step, "failed", message))
        status_code = 400 if isinstance(exc, ValueError) else 500
        raise AnalysisPipelineError(
            step,
            message,
            logs,
            status_code=status_code,
        ) from exc

    logs.append(_log(step, "success", success_message(updates)))
    return {**updates, "process_logs": logs}


def extract_text_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        filename = state.get("filename", "").strip()
        file_bytes = state.get("file_bytes", b"")
        if not filename:
            raise ValueError("업로드한 파일 이름을 확인할 수 없습니다.")
        if not file_bytes:
            raise ValueError("업로드한 파일이 비어 있습니다.")

        text = extract_text(file_bytes, filename)
        if not text.strip():
            raise ValueError("계약서에서 분석할 텍스트를 추출하지 못했습니다.")
        return {"text": text}

    return _run_node(
        state,
        "extract_text",
        operation,
        lambda updates: f"계약서 텍스트 추출 완료 ({len(updates['text'])}자)",
    )


def resolve_contract_type_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        requested_type = state.get("requested_contract_type", "자동 감지")
        if requested_type == "자동 감지":
            detected_type = detect_contract_type(state["text"])
            return {
                "detected_type": detected_type,
                "resolved_type": detected_type,
            }
        return {"detected_type": None, "resolved_type": requested_type}

    return _run_node(
        state,
        "resolve_contract_type",
        operation,
        lambda updates: f"계약 유형 결정 완료 ({updates['resolved_type']})",
    )


def split_clauses_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        clauses = split_clauses(state["text"])
        if not clauses:
            raise ValueError("분석 가능한 계약 조항을 찾지 못했습니다.")
        return {"clauses": clauses}

    return _run_node(
        state,
        "split_clauses",
        operation,
        lambda updates: f"계약 조항 분리 완료 ({len(updates['clauses'])}개)",
    )


def analyze_clauses_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        analysis = analyze_clauses(state["clauses"], state["resolved_type"])
        return {"analysis": analysis}

    return _run_node(
        state,
        "analyze_clauses",
        operation,
        lambda updates: (
            "조항별 위험 분석 완료 "
            "(위험 조항 "
            f"{sum(isinstance(item, dict) and item.get('is_risky') is True for item in updates['analysis'])}개)"
        ),
    )


def has_risky_clause(state: AnalysisState) -> Literal["risky", "safe"]:
    return (
        "risky"
        if any(
            isinstance(item, dict) and item.get("is_risky") is True
            for item in state.get("analysis", [])
        )
        else "safe"
    )


def route_by_risk_node(state: AnalysisState) -> dict:
    risky_count = sum(
        isinstance(item, dict) and item.get("is_risky") is True
        for item in state.get("analysis", [])
    )
    return _run_node(
        state,
        "has_risky_clause",
        lambda: {},
        lambda _: (
            f"위험 조항 {risky_count}개 확인: 위험도 분류 및 요약 경로 실행"
            if risky_count
            else "위험 조항 없음: 분류 및 LLM 요약 생략 경로 실행"
        ),
    )


def classify_risk_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        classified = classify_risk(
            state.get("analysis", []),
            state.get("resolved_type", "기타"),
        )
        return {"classified": classified}

    return _run_node(
        state,
        "classify_risk",
        operation,
        lambda updates: (
            "위험 조항이 있어 위험도 분류 실행 "
            f"({len(updates['classified'])}개 조항)"
        ),
    )


def summarize_node(state: AnalysisState) -> dict:
    return _run_node(
        state,
        "summarize",
        lambda: {"summary": summarize(state.get("classified", []))},
        lambda _: "위험 조항 전체 요약 생성 완료",
    )


def build_safe_result_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        safe_clauses = []
        for item in state.get("analysis", []):
            normalized = item if isinstance(item, dict) else {}
            safe_clauses.append(
                {
                    **normalized,
                    "clause": str(normalized.get("clause", "")).strip(),
                    "is_risky": False,
                    "reason": str(
                        normalized.get("reason") or "위험 요소가 확인되지 않았습니다."
                    ).strip(),
                    "risk_level": "low",
                }
            )
        return {
            "classified": safe_clauses,
            "summary": get_no_risk_summary(),
        }

    return _run_node(
        state,
        "build_safe_result",
        operation,
        lambda _: "위험 조항이 없어 분류 및 LLM 요약을 생략하고 기본 요약 생성",
    )


def finalize_node(state: AnalysisState) -> dict:
    def operation() -> dict:
        result = {
            "contract_type": state["resolved_type"],
            "detected_type": state.get("detected_type"),
            "clauses": state.get("classified", []),
            "summary": state.get("summary", get_no_risk_summary()),
        }
        return {"result": result}

    updates = _run_node(
        state,
        "finalize",
        operation,
        lambda _: "분석 결과 응답 생성 완료",
    )
    updates["result"]["process_logs"] = updates["process_logs"]
    return updates


def _build_analysis_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("extract_text", extract_text_node)
    graph.add_node("resolve_contract_type", resolve_contract_type_node)
    graph.add_node("split_clauses", split_clauses_node)
    graph.add_node("analyze_clauses", analyze_clauses_node)
    graph.add_node("route_by_risk", route_by_risk_node)
    graph.add_node("classify_risk", classify_risk_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("build_safe_result", build_safe_result_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "extract_text")
    graph.add_edge("extract_text", "resolve_contract_type")
    graph.add_edge("resolve_contract_type", "split_clauses")
    graph.add_edge("split_clauses", "analyze_clauses")
    graph.add_edge("analyze_clauses", "route_by_risk")
    graph.add_conditional_edges(
        "route_by_risk",
        has_risky_clause,
        {
            "risky": "classify_risk",
            "safe": "build_safe_result",
        },
    )
    graph.add_edge("classify_risk", "summarize")
    graph.add_edge("summarize", "finalize")
    graph.add_edge("build_safe_result", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


analysis_graph = _build_analysis_graph()


def _apply_node(
    state: AnalysisState,
    step: str,
    node,
):
    yield {
        "event": "step_started",
        "step": step,
        "message": "처리 중입니다.",
    }
    updates = node(state)
    state.update(updates)
    log = state.get("process_logs", [])[-1]
    yield {
        "event": "step_finished",
        "step": log["step"],
        "status": log["status"],
        "message": log["message"],
        "log": log,
    }


def _skip_step(step: str, message: str) -> dict:
    return {
        "event": "step_skipped",
        "step": step,
        "status": "skipped",
        "message": message,
    }


def iter_analysis_pipeline_events(
    file_bytes: bytes,
    filename: str,
    contract_type: str,
):
    state: AnalysisState = {
        "file_bytes": file_bytes,
        "filename": filename,
        "requested_contract_type": contract_type,
        "process_logs": [],
    }

    common_nodes = [
        ("extract_text", extract_text_node),
        ("resolve_contract_type", resolve_contract_type_node),
        ("split_clauses", split_clauses_node),
        ("analyze_clauses", analyze_clauses_node),
        ("has_risky_clause", route_by_risk_node),
    ]
    for step, node in common_nodes:
        yield from _apply_node(state, step, node)

    if has_risky_clause(state) == "risky":
        yield from _apply_node(state, "classify_risk", classify_risk_node)
        yield from _apply_node(state, "summarize", summarize_node)
        yield _skip_step(
            "build_safe_result",
            "위험 조항이 있어 안전 기본 요약 경로는 실행하지 않았습니다.",
        )
    else:
        yield _skip_step(
            "classify_risk",
            "위험 조항이 없어 위험도 분류를 실행하지 않았습니다.",
        )
        yield _skip_step(
            "summarize",
            "위험 조항이 없어 LLM 위험 요약을 실행하지 않았습니다.",
        )
        yield from _apply_node(state, "build_safe_result", build_safe_result_node)

    yield from _apply_node(state, "finalize", finalize_node)
    yield {
        "event": "completed",
        "result": state["result"],
        "process_logs": state.get("process_logs", []),
    }


def run_analysis_pipeline(
    file_bytes: bytes,
    filename: str,
    contract_type: str,
) -> dict:
    initial_state: AnalysisState = {
        "file_bytes": file_bytes,
        "filename": filename,
        "requested_contract_type": contract_type,
        "process_logs": [],
    }
    final_state = analysis_graph.invoke(initial_state)
    return final_state["result"]

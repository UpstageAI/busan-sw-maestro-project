"""단일 LangGraph interrupt/resume 통합 테스트.

build_graph 는 lru_cache + MemorySaver 이므로 테스트마다 고유 thread_id 를 쓴다.
"""

from langgraph.types import Command

from app.agent.graph import build_graph


def _cfg(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_graph_interrupts_for_approval(seeded_db):
    graph = build_graph()
    result = graph.invoke(
        {
            "session_id": "t-graph-1",
            "items": [
                {
                    "type": "task",
                    "title": "발표자료 만들기",
                    "assignee": "박성종",
                    "due_date": "2026-06-06",
                },
                {"type": "ignore", "title": "잡담"},
            ],
        },
        _cfg("t-graph-1"),
    )
    interrupts = result.get("__interrupt__")
    assert interrupts is not None
    payload = interrupts[0].value
    assert payload["reason"] == "awaiting_approval"
    assert len(payload["reviewables"]) == 1  # task 1건
    assert len(payload["skipped"]) == 1  # ignore 1건
    # seed 와 동일 작업이라 중복 검출
    assert payload["reviewables"][0]["conflict"]["has_conflict"] is True


def test_graph_resume_executes_and_finalizes(seeded_db):
    graph = build_graph()
    graph.invoke(
        {
            "session_id": "t-graph-2",
            "items": [{"type": "task", "title": "신규작업", "assignee": "이우태"}],
        },
        _cfg("t-graph-2"),
    )
    result = graph.invoke(
        Command(resume=[{"item_id": "item-0", "action": "approve"}]),
        _cfg("t-graph-2"),
    )
    assert result.get("__interrupt__") is None
    assert result["summary"]["executed"] == 1
    assert result.get("final_output") is not None


def test_graph_skips_approval_when_all_ignored(seeded_db):
    graph = build_graph()
    result = graph.invoke(
        {"session_id": "t-graph-3", "items": [{"type": "ignore", "title": "x"}]},
        _cfg("t-graph-3"),
    )
    # 검토 대상 없음 -> 승인 interrupt 건너뛰고 바로 종료
    assert result.get("__interrupt__") is None
    assert "final_output" in result

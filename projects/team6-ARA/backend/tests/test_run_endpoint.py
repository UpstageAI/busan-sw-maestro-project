"""POST /run, /resume 및 보조 엔드포인트 통합 테스트.

build_graph 가 프로세스 공유 MemorySaver 라서 테스트마다 고유 session_id 를 쓴다.
"""


def _run_one(client, session_id, item):
    return client.post(
        "/run", json={"session_id": session_id, "items": [item]}
    ).json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_mock_seed(client):
    body = client.post("/mock/seed").json()
    assert body["seeded"]["calendar_events"] == 1
    assert body["seeded"]["tasks"] == 1


def test_run_conflict_scenario(seeded_client):
    r = seeded_client.post("/mock/run/conflict").json()
    assert r["status"] == "awaiting_approval"
    assert r["reviewables"][0]["conflict"]["kind"] == "calendar_overlap"
    assert r["reviewables"][0]["conflict"]["has_conflict"] is True


def test_run_multi_scenario(seeded_client):
    r = seeded_client.post("/mock/run/multi").json()
    assert r["status"] == "awaiting_approval"
    assert len(r["reviewables"]) == 4  # task 3 + calendar 1
    dup = [x for x in r["reviewables"] if x["item"]["id"] == "m-1"][0]
    assert dup["conflict"]["has_conflict"] is True  # 발표자료(박성종) seed 중복


def test_run_vague_risk_scenario(seeded_client):
    r = seeded_client.post("/mock/run/vague_risk").json()
    kinds = {x["item"]["type"] for x in r["reviewables"]}
    assert kinds == {"pending", "risk"}
    assert all(not x["conflict"]["has_conflict"] for x in r["reviewables"])


def test_run_assigns_ids_when_missing(client):
    r = _run_one(client, "s-ids", {"type": "task", "title": "A"})
    assert r["reviewables"][0]["item"]["id"] == "item-0"


def test_resume_approve_stores(client):
    _run_one(client, "s-approve", {"type": "task", "title": "신규", "assignee": "A"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-approve",
            "decisions": [{"item_id": "item-0", "action": "approve"}],
        },
    ).json()
    assert out["status"] == "completed"
    assert out["summary"]["executed"] == 1
    assert client.get("/storage/tasks").json()["count"] == 1


def test_resume_exclude_does_not_store(client):
    _run_one(client, "s-exclude", {"type": "task", "title": "신규", "assignee": "A"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-exclude",
            "decisions": [{"item_id": "item-0", "action": "exclude"}],
        },
    ).json()
    assert out["summary"]["excluded"] == 1
    assert client.get("/storage/tasks").json()["count"] == 0


def test_resume_modify_recheck_and_no_store(client):
    _run_one(client, "s-modify", {"type": "task", "title": "원본", "assignee": "A"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-modify",
            "decisions": [
                {
                    "item_id": "item-0",
                    "action": "modify",
                    "modified_item": {
                        "id": "item-0",
                        "type": "task",
                        "title": "수정본",
                        "assignee": "A",
                    },
                }
            ],
        },
    ).json()
    res = out["results"][0]
    assert res["status"] == "needs_recheck"
    assert res["recheck_required"] is True
    assert client.get("/storage/tasks").json()["count"] == 0  # 저장 안 됨
    # 6-3 seam: 수정 쌍이 final_output.needs_recheck 에 잡힌다
    assert len(out["final_output"]["needs_recheck"]) == 1


def test_resume_missing_required_falls_back_to_pending(client):
    # calendar 는 title+date 필수. date 누락 -> pending 폴백(저장됨), status=pending.
    _run_one(client, "s-missing", {"type": "calendar", "title": "날짜없는 일정"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-missing",
            "decisions": [{"item_id": "item-0", "action": "approve"}],
        },
    ).json()
    assert out["results"][0]["status"] == "pending"
    assert client.get("/storage/pending_queue").json()["count"] == 1
    assert client.get("/storage/calendar_events").json()["count"] == 0


def test_resume_tool_failure_falls_back_to_pending(client, monkeypatch):
    from app.schemas.items import ToolName
    from app.tools import TOOL_REGISTRY

    def _boom(**kwargs):
        raise RuntimeError("강제 실패")

    monkeypatch.setitem(TOOL_REGISTRY, ToolName.create_task, _boom)

    _run_one(client, "s-fail", {"type": "task", "title": "터질 작업", "assignee": "A"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-fail",
            "decisions": [{"item_id": "item-0", "action": "approve"}],
        },
    ).json()
    res = out["results"][0]
    assert res["status"] == "pending"
    assert "강제 실패" in res["error"]
    assert client.get("/storage/pending_queue").json()["count"] == 1


def test_run_all_ignored_completes_without_approval(client):
    r = client.post(
        "/run",
        json={"session_id": "s-ignore", "items": [{"type": "ignore", "title": "잡담"}]},
    ).json()
    # 검토 대상 없음 -> 승인 없이 즉시 완료
    assert r["status"] == "completed"


def test_unknown_scenario_404(client):
    assert client.post("/mock/run/nope").status_code == 404


def test_unknown_storage_kind_404(client):
    assert client.get("/storage/nope").status_code == 404

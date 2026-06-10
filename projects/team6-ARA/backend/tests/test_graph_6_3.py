"""6-3 단일 그래프 흡수 흐름 테스트 (2단계 HITL).

흐름: /run -> 1차 승인 interrupt -> /resume(decisions) -> execution -> feedback_seam
      -> feedback_analyze -> [후보 있으면] 2차 선호 interrupt -> /resume(choices) -> completed

DB 격리(storage/feedback/preferences)는 conftest fixture 가 처리한다.
"""

from app.feedback.db import load_user_preferences


def _run_one(client, session_id, item):
    return client.post(
        "/run", json={"session_id": session_id, "items": [item]}
    ).json()


def test_approve_only_no_preference_interrupt(client):
    # 수정 없이 승인만 -> 후보 없음 -> 2차 interrupt 없이 바로 completed.
    _run_one(client, "s-appr", {"type": "task", "title": "발표자료", "assignee": "A"})
    out = client.post(
        "/resume",
        json={
            "session_id": "s-appr",
            "decisions": [{"item_id": "item-0", "action": "approve"}],
        },
    ).json()
    assert out["status"] == "completed"
    assert out["results"][0]["status"] == "success"
    assert client.get("/storage/tasks").json()["count"] == 1


def test_modify_triggers_preference_and_save(client):
    # 수정 -> 2차 선호 interrupt -> save 선택 -> User Preference 저장.
    _run_one(client, "s-pref", {"type": "memo", "title": "기획서 다시 보기"})
    out1 = client.post(
        "/resume",
        json={
            "session_id": "s-pref",
            "decisions": [
                {
                    "item_id": "item-0",
                    "action": "modify",
                    "modified_item": {
                        "id": "item-0",
                        "type": "task",  # memo -> task 로 분류 변경
                        "title": "기획서 다시 보기",
                    },
                }
            ],
        },
    ).json()
    assert out1["status"] == "awaiting_preference"
    # type 변경이 후보로 잡힌다.
    fields = {c["field"] for c in out1["candidates"]}
    assert "type" in fields
    type_cand = next(c for c in out1["candidates"] if c["field"] == "type")
    assert type_cand["original"] == "memo"
    assert type_cand["preferred"] == "task"

    # 2차 resume: type 후보를 save.
    out2 = client.post(
        "/resume",
        json={
            "session_id": "s-pref",
            "preference_choices": [
                {
                    "field": "type",
                    "action": "save",
                    "original": "memo",
                    "preferred": "task",
                }
            ],
        },
    ).json()
    assert out2["status"] == "completed"
    assert out2["confirmed_output"]["saved"] is True
    assert "type" in out2["confirmed_output"]["saved_fields"]

    # User Preference Store 에 저장 확인.
    prefs = load_user_preferences()
    assert any(p["field"] == "type" for p in prefs)


def test_modify_preference_dismiss_no_save(client):
    # 수정 -> 2차 선호 interrupt -> dismiss -> 저장 안 됨.
    _run_one(client, "s-dis", {"type": "memo", "title": "메모 항목"})
    out1 = client.post(
        "/resume",
        json={
            "session_id": "s-dis",
            "decisions": [
                {
                    "item_id": "item-0",
                    "action": "modify",
                    "modified_item": {
                        "id": "item-0",
                        "type": "task",
                        "title": "메모 항목",
                    },
                }
            ],
        },
    ).json()
    assert out1["status"] == "awaiting_preference"

    out2 = client.post(
        "/resume",
        json={
            "session_id": "s-dis",
            "preference_choices": [{"field": "type", "action": "dismiss"}],
        },
    ).json()
    assert out2["status"] == "completed"
    assert out2["confirmed_output"]["saved"] is False
    assert load_user_preferences() == []

"""세션 진척도 노드(load_state·reconcile·persist_state) 테스트.

load/persist는 SessionLocal을 SQLite 인메모리로 교체해 검증하고,
reconcile은 인벤토리 델타 계산이 결정론이라 그대로 검증한다.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401  Base.metadata에 테이블 등록
from app.agents import session_memory
from app.prompts.templates import format_progress_block


@pytest.fixture
def sqlite_db(monkeypatch):
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_memory, "SessionLocal", sessionmaker(bind=engine, future=True))


def test_저장한_진척도를_다음_턴에_로드한다(sqlite_db):
    session_memory.persist_state({
        "thread_id": "t1",
        "goal_key": "minecraft:iron_pickaxe",
        "inventory": [{"item": "minecraft:oak_log", "count": 5}],
        "inventory_connected": True,
    })
    loaded = session_memory.load_state({"thread_id": "t1"})
    assert loaded["prior_goal_key"] == "minecraft:iron_pickaxe"
    assert loaded["prior_last_inventory"] == [{"item": "minecraft:oak_log", "count": 5}]


def test_목표없는_턴은_직전_목표를_유지한다(sqlite_db):
    session_memory.persist_state({"thread_id": "t1", "goal_key": "minecraft:furnace",
                                  "inventory": [], "inventory_connected": True})
    # 다음 턴: 목표 미해석(goal_key 없음) + 직전 목표 로드 상태로 저장
    session_memory.persist_state({"thread_id": "t1", "goal_key": "",
                                  "prior_goal_key": "minecraft:furnace",
                                  "inventory": [], "inventory_connected": True})
    assert session_memory.load_state({"thread_id": "t1"})["prior_goal_key"] == "minecraft:furnace"


def test_없는_세션은_빈_진척도를_반환한다(sqlite_db):
    # 유효 thread_id지만 저장된 게 없으면 빈 prior로 채워 반환한다.
    assert session_memory.load_state({"thread_id": "nope"}) == {
        "prior_goal_key": "", "prior_last_inventory": [], "prior_plan": [], "prior_completed": [],
    }


def test_thread_id_없으면_skip():
    assert session_memory.load_state({}) == {}
    assert session_memory.persist_state({}) == {}


def test_reconcile_새로_얻은_재료를_집어낸다():
    out = session_memory.reconcile({
        "prior_last_inventory": [{"item": "minecraft:cobblestone", "count": 1}],
        "inventory": [{"item": "minecraft:cobblestone", "count": 4}, {"item": "minecraft:raw_iron", "count": 2}],
    })
    note = {p["item"]: p["count"] for p in out["progress_note"]}
    assert note["minecraft:cobblestone"] == 3
    assert note["minecraft:raw_iron"] == 2


def test_reconcile_첫_턴이나_변화없으면_빈값():
    assert session_memory.reconcile({"prior_last_inventory": [], "inventory": [{"item": "x", "count": 1}]}) == {}
    same = [{"item": "minecraft:dirt", "count": 3}]
    assert session_memory.reconcile({"prior_last_inventory": same, "inventory": same}) == {}


def test_진행_블록_포맷():
    block = format_progress_block([{"item": "minecraft:cobblestone", "count": 3}])
    assert "조약돌 3개" in block
    assert format_progress_block([]) == ""


# --- reconcile 심화: plan 단계별 완료 + 다음 단계 ---

def test_reconcile_같은_목표면_완료단계와_다음단계를_낸다():
    # 직전 plan엔 조약돌·막대기가 있었는데, 이번 plan(gather)엔 막대기만 남음 → 조약돌 완료.
    out = session_memory.reconcile({
        "prior_goal_key": "minecraft:stone_pickaxe",
        "goal_key": "minecraft:stone_pickaxe",
        "prior_plan": [{"item": "minecraft:cobblestone", "qty": 3}, {"item": "minecraft:stick", "qty": 2}],
        "prior_completed": [],
        "material_plan": {"ready": False, "gather": [{"item": "minecraft:stick", "qty": 2, "blocked": False}]},
    })
    assert out["completed_steps"] == ["minecraft:cobblestone"]
    assert out["goal_completed"] == ["minecraft:cobblestone"]
    assert out["next_step"] == {"kind": "gather", "item": "minecraft:stick", "qty": 2, "blocked": False}


def test_reconcile_목표가_바뀌면_완료누적을_초기화한다():
    out = session_memory.reconcile({
        "prior_goal_key": "minecraft:furnace",
        "goal_key": "minecraft:stone_pickaxe",
        "prior_plan": [{"item": "minecraft:cobblestone", "qty": 8}],
        "prior_completed": ["minecraft:cobblestone"],
        "material_plan": {"ready": True, "gather": []},
    })
    assert "completed_steps" not in out          # 직전 plan은 다른 목표 것이라 무시
    assert out["goal_completed"] == []
    assert out["next_step"] == {"kind": "craft"}


def test_reconcile_제작목표_없으면_단계추적_생략():
    out = session_memory.reconcile({
        "prior_last_inventory": [{"item": "minecraft:dirt", "count": 1}],
        "inventory": [{"item": "minecraft:dirt", "count": 5}],
        # goal_key 없음(생존·탐험 등)
    })
    assert out.get("progress_note")            # 인벤 델타는 여전히 잡음
    assert "next_step" not in out and "goal_completed" not in out


def test_persist_load로_plan과_완료가_왕복한다(sqlite_db):
    session_memory.persist_state({
        "thread_id": "t9",
        "goal_key": "minecraft:stone_pickaxe",
        "inventory": [],
        "inventory_connected": True,
        "material_plan": {"gather": [{"item": "minecraft:stick", "qty": 2}]},
        "goal_completed": ["minecraft:cobblestone"],
    })
    loaded = session_memory.load_state({"thread_id": "t9"})
    assert loaded["prior_plan"] == [{"item": "minecraft:stick", "qty": 2}]
    assert loaded["prior_completed"] == ["minecraft:cobblestone"]

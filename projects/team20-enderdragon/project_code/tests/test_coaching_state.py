"""coaching_state 저장소(repositories) 테스트.

세션별 코칭 진척도 스냅샷이 저장/조회/갱신되는지 SQLite 인메모리로 검증한다.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401  Base.metadata에 테이블 등록
from app import repositories


@pytest.fixture
def db():
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        yield session
    finally:
        session.close()


def test_저장한_진척도를_그대로_조회한다(db):
    snapshot = {
        "current_goal": "철 곡괭이",
        "goal_key": "minecraft:iron_pickaxe",
        "plan": [{"id": "s1", "title": "조약돌 캐기", "status": "active"}],
        "completed": [],
        "last_inventory": [{"item": "minecraft:oak_log", "count": 5}],
    }
    repositories.upsert_coaching_state(db, "t1", snapshot)
    loaded = repositories.get_coaching_state(db, "t1")
    assert loaded == snapshot


def test_같은_세션은_덮어쓴다(db):
    repositories.upsert_coaching_state(db, "t1", {"current_goal": "A"})
    repositories.upsert_coaching_state(db, "t1", {"current_goal": "B", "completed": ["s1"]})
    loaded = repositories.get_coaching_state(db, "t1")
    assert loaded["current_goal"] == "B"
    assert loaded["completed"] == ["s1"]


def test_없는_세션은_None(db):
    assert repositories.get_coaching_state(db, "missing") is None


def test_세션마다_독립적이다(db):
    repositories.upsert_coaching_state(db, "t1", {"current_goal": "철 곡괭이"})
    repositories.upsert_coaching_state(db, "t2", {"current_goal": "첫 밤 넘기기"})
    assert repositories.get_coaching_state(db, "t1")["current_goal"] == "철 곡괭이"
    assert repositories.get_coaching_state(db, "t2")["current_goal"] == "첫 밤 넘기기"

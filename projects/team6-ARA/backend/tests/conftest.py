"""테스트 공통 fixture.

각 테스트는 tmp DB 를 주입받아 실제 storage.db 를 오염시키지 않는다.
configure_db_path() 훅으로 경로를 격리한다 (env var 대신 명시 훅).
"""

import pytest
from fastapi.testclient import TestClient

from app.storage.db import configure_db_path, init_db
from app.storage.seed import seed_if_empty


@pytest.fixture(autouse=True)
def isolate_6_3_db(tmp_path, monkeypatch):
    """6-3(feedback/preferences) DB 를 tmp 로 격리한다 (모든 테스트 자동 적용).

    storage.db 는 configure_db_path() 훅으로 격리되지만 feedback.db/preferences.db 는
    모듈 상수 _DB_PATH 라 별도로 막아야 한다. 그래프가 6-3 노드에서 이 DB 에 쓰므로
    격리 없이는 실제 backend/feedback.db, backend/preferences.db 가 오염된다.
    """
    monkeypatch.setattr("app.feedback.db._DB_PATH", tmp_path / "feedback.db")
    monkeypatch.setattr("app.preferences.store._DB_PATH", tmp_path / "preferences.db")


@pytest.fixture
def tmp_db(tmp_path):
    """테스트별 tmp SQLite DB 경로를 주입한다."""
    db_file = tmp_path / "test_storage.db"
    configure_db_path(db_file)
    init_db()
    yield db_file
    configure_db_path(None)


@pytest.fixture
def seeded_db(tmp_db):
    """시연용 기존 데이터가 들어간 tmp DB."""
    seed_if_empty()
    return tmp_db


@pytest.fixture
def client(tmp_db):
    """tmp DB 가 적용된 TestClient (seed 없음)."""
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def seeded_client(seeded_db):
    """시연 데이터가 들어간 TestClient."""
    from app.main import app

    with TestClient(app) as c:
        yield c

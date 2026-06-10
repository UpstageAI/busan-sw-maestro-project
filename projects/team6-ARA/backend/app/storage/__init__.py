"""6-2 Mock 저장소 (SQLite).

- db: 커넥션 + 스키마 (env var ACTION_ROUTER_DB_PATH 로 경로 주입 가능)
- seed: 충돌 시연용 기존 데이터 (명시적 호출 전용, 일반 경로 자동 실행 금지)
- queries: 충돌 검사용 조회
"""

from app.storage.db import db_path, get_conn, init_db
from app.storage.queries import (
    list_table,
    load_calendar_events,
    load_tasks,
)
from app.storage.seed import seed_if_empty

__all__ = [
    "db_path",
    "get_conn",
    "init_db",
    "list_table",
    "load_calendar_events",
    "load_tasks",
    "seed_if_empty",
]

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

# MySQL 엔진. pool_pre_ping으로 끊긴 커넥션 자동 복구.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """SQLAlchemy 선언적 모델의 베이스. 모든 모델이 상속한다."""


def get_session():
    """요청 단위 DB 세션을 열고 사용 후 닫는다 (FastAPI 의존성 등에서 사용)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

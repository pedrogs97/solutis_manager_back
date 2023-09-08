"""Database connection"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
_session_db = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_engine,
)


def get_db_session() -> Session:
    """Return session"""
    return _session_db()

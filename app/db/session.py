"""Database session and engine configuration.

Uses SQLAlchemy 2.x with a synchronous engine (psycopg2 driver) for Week 1.
Async support (asyncpg) can be layered in when async endpoints are needed.

No models are defined here yet; this module only provides the session factory
and a dependency function for use in FastAPI route handlers.
"""
import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models.

    All model classes (defined in app/models/) should inherit from this.
    """


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return False
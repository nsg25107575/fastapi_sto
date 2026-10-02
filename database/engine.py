import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import Config


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models
    """
    pass


def _build_engine_kwargs() -> dict:
    """
    Pool-tuning kwargs (pool_size/max_overflow/pool_timeout/pool_recycle)
    only apply to QueuePool-based dialects (MariaDB/MySQL/Postgres, etc.).
    SQLite (used by the test suite and local sqlite:// fallback) uses
    SingletonThreadPool/StaticPool, which reject these kwargs outright.
    """
    if Config.db_url.startswith("sqlite"):
        return {}

    return dict(
        pool_size=int(os.getenv("DB_POOL_SIZE", 10)),
        max_overflow=int(os.getenv("DB_POOL_MAX_OVERFLOW", 20)),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", 30)),
        # Recycle connections periodically to avoid stale/dropped connections
        # (MariaDB default wait_timeout is 28800s, we recycle well before that).
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", 1800)),
        # Validate connections with a lightweight ping before use — avoids
        # errors from connections dropped by the DB or a load balancer.
        pool_pre_ping=True,
    )


# Connection pool tuned for high concurrency under multiple uvicorn workers.
# Each worker process gets its own pool, so keep per-worker size moderate —
# total DB connections ≈ UVICORN_WORKERS * (pool_size + max_overflow).
# Make sure this stays below MariaDB's max_connections (see docker-compose.yml).
engine = create_engine(Config.db_url, **_build_engine_kwargs())
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_session():
    """
    Provides a database session and closes it after use.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import Config


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models
    """
    pass

engine = create_engine(Config.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """
    Provides a database session and closes it after use.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

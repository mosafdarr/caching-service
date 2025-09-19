"""Database engine and session management.

This module sets up the SQLAlchemy engine and session factory,
and provides a context-managed dependency for database sessions.

Attributes:
    engine (Engine): SQLAlchemy engine created using DATABASE_URL.
    SessionLocal (sessionmaker): Configured session factory for DB access.

Functions:
    get_session(): Context-managed database session dependency for use
        in application code and FastAPI dependencies.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import settings

# Create Engine
engine = create_engine(settings.DATABASE_URL)

# Create Session factory
SessionLocal = sessionmaker(autocommit=False, bind=engine)


@contextmanager
def get_session():
    """Provide a transactional database session scope.

    Yields:
        Session: SQLAlchemy session object.

    Raises:
        Exception: Any exception raised during DB operations will
        trigger a rollback before being re-raised.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

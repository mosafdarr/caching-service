"""Database schema definitions for the Caching Service.

This module defines the SQLAlchemy base class, mixins, and example tables.
Currently includes a reusable timestamp mixin and a placeholder `User` model.

Classes:
    Base: Declarative base for all ORM models.
    TimestampMixin: Provides created_at and updated_at columns.
    User: Example user table (to be replaced with actual caching service models).
"""

from sqlalchemy import Column, Integer, String, Boolean
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All ORM models in the project should inherit from this class.
    """
    pass


class TimestampMixin:
    """Reusable mixin that adds created_at and updated_at columns.

    Attributes:
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        server_onupdate=func.now(),
        nullable=False,
    )


# TODO: Remove this dummy user table and add actual tables needed for caching service.
class User(TimestampMixin, Base):
    """Example user table (placeholder).

    Attributes:
        id (int): Primary key.
        email (str): Unique email address of the user.
        hashed_password (str): Hashed password for authentication.
        is_active (bool): Indicates whether the user account is active.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

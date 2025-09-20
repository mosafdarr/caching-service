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


class cache_payloads(Base, TimestampMixin):
    """Example cache payload table.

    This is a placeholder table definition for the caching service.
    It should be replaced with actual models relevant to caching operations.

    Attributes:
        id (int): Primary key identifier.
        input_payload (str): Input payload data.
        output_payload (str): Output payload data.
    """

    __tablename__ = "cache_payloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payload_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    input_payload: Mapped[str] = mapped_column(String(255), nullable=False)
    output_payload: Mapped[str] = mapped_column(String(255), nullable=False)

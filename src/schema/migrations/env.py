"""Alembic migration environment configuration.

This module configures Alembic for running database schema migrations,
both in 'offline' and 'online' modes. It integrates SQLAlchemy's metadata
from the application's models, enabling autogeneration of migration files.

Key Concepts:
    - Offline mode: Emits SQL statements directly without needing a live DB connection.
    - Online mode: Establishes a DB engine/connection and runs migrations directly.

Behavior:
    - If `sqlalchemy.url` is set in alembic.ini it will be used.
    - If `sqlalchemy.url` is empty in alembic.ini, this module will attempt
      to read DATABASE_URL from your application's Settings (Pydantic).
      This allows you to keep environment-driven configuration in one place
      (your `.env` / settings.py) while keeping alembic.ini at project root.

Note:
    Importing application settings is performed lazily inside functions to
    avoid potential circular import issues during Alembic's bootstrap.
"""

from __future__ import annotations

from logging.config import fileConfig
from typing import Dict, Optional

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import your application's metadata (Base) used for autogeneration.
from src.schema.tables import Base  # type: ignore

# Alembic Config object, provides access to the values within alembic.ini.
config = context.config

# Configure Python logging using alembic.ini (if present).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def _get_database_url_from_settings() -> Optional[str]:
    """Lazily import and return the application's DATABASE_URL.

    The lazy import prevents circular imports when Alembic boots up.
    Returns:
        The DB URL string from src.settings.settings.DATABASE_URL or None.
    """
    try:
        # local import to avoid circular import issues
        from src.settings import settings  # type: ignore

        return getattr(settings, "DATABASE_URL", None)
    except Exception:
        # On failure, return None and allow alembic.ini value to be used.
        return None


def _determine_database_url() -> Optional[str]:
    """Determine DB URL to use for migrations.

    Priority:
      1. `sqlalchemy.url` from alembic.ini, if present and non-empty.
      2. `DATABASE_URL` from application settings (via Pydantic Settings).
      3. None (Alembic will error if a URL is required and none is provided).
    """
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url and ini_url.strip():
        return ini_url.strip()

    settings_url = _get_database_url_from_settings()
    if settings_url and settings_url.strip():
        # if we got it from settings, set it back onto alembic config so
        # engine_from_config can pick it up uniformly.
        config.set_main_option("sqlalchemy.url", settings_url.strip())
        return settings_url.strip()

    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with a database URL, without creating an Engine.
    No DBAPI is required. Migration commands emit SQL directly to stdout
    (or configured script output). This is useful for generating SQL scripts
    without a live DB connection.
    """
    url = _determine_database_url()
    if not url:
        raise RuntimeError(
            "No database URL found. Set `sqlalchemy.url` in alembic.ini "
            "or provide DATABASE_URL in application settings."
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a live DB connection with the migration
    context, allowing migrations to run against the actual database.
    """
    # Ensure DB URL is available and present in alembic config for engine_from_config
    db_url = _determine_database_url()
    if not db_url:
        raise RuntimeError(
            "No database URL found. Set `sqlalchemy.url` in alembic.ini "
            "or provide DATABASE_URL in application settings."
        )

    # Provide a default empty dict to engine_from_config to avoid None errors.
    alembic_section: Dict[str, str] = config.get_section(config.config_ini_section) or {}

    connectable = engine_from_config(
        alembic_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Entry point: choose offline/online execution mode.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

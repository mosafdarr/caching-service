"""Alembic migration environment configuration.

This module configures Alembic for running database schema migrations,
both in 'offline' and 'online' modes. It integrates SQLAlchemy's metadata
from the application's models, enabling autogeneration of migration files.

Key Concepts:
    - Offline mode: Emits SQL statements directly without needing a live DB connection.
    - Online mode: Establishes a DB engine/connection and runs migrations directly.

Attributes:
    config (Config): Alembic configuration object loaded from alembic.ini.
    target_metadata (MetaData): SQLAlchemy metadata from the application's Base.

Functions:
    run_migrations_offline(): Configure and run migrations without a DB connection.
    run_migrations_online(): Configure and run migrations with a DB connection.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from src.schema.tables import Base

# Alembic Config object, provides access to .ini file values.
config = context.config

# Set up Python logging via Alembic config file.
fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    Configures the context with a database URL, without creating
    an Engine. No DBAPI is required. Migration commands emit SQL
    directly to the script output.

    This is useful for generating SQL scripts without a live DB.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    Creates an Engine and associates a live DB connection with
    the migration context, allowing migrations to run against
    the actual database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Entry point: choose offline/online execution mode.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""Application settings and database helpers for the Caching Service.

This module centralizes configuration using Pydantic Settings (v2),
providing typed, environment-driven configuration with sensible defaults.

Environment:
    PROJECT_NAME (str): Human-readable project name. Default: "Caching Service".
    DATABASE_URL (str): SQLAlchemy/DB URL.
    DATABASE_ENGINE_ECHO (bool): Whether to echo SQL. Default: True (disable in prod).
    TIMEOUT (int): Generic timeout for outbound calls, in seconds. Default: 30.
    LOG_LEVEL (str): Global log level. Default: "INFO".
    CORS_ORIGINS (json-list): Allowed origins (JSON array). Default: ["*"].

Example:
    # .env
    PROJECT_NAME="Caching Service"
    DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/integrationdb"
    CORS_ORIGINS='["http://localhost:3000"]'
"""

from __future__ import annotations

from typing import Iterator

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment."""

    PROJECT_NAME: str = Field(default="Caching Service", env="PROJECT_NAME")

    # Databases & SQLAlchemy
    DATABASE_URL: str = Field(
        default="postgresql://postgres:mosafdar%40123@localhost:5432/integrationdb",
        env="DATABASE_URL",
    )
    DATABASE_ENGINE_ECHO: bool = Field(
        default=True, env="DATABASE_ENGINE_ECHO"
    )  # Set to False in production.

    # Generic timeouts
    TIMEOUT: int = Field(default=30, env="TIMEOUT")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Security
    CORS_ORIGINS: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DatabaseConfig(BaseSettings):
    """Database utilities wrapper.

    Provides a typed generator for dependency-injected DB sessions.

    Methods:
        get_session: Yields a database session for use in FastAPI dependencies.
    """

    @classmethod
    def get_session(cls):
        """Yield a database session (FastAPI dependency-friendly).

        Yields:
            object: An active DB session object from `schema.database.get_session`.
        """
        from schema.database import get_session  # Lazy import to avoid circular deps

        with get_session() as session:
            yield session


# Module-level singletons
settings = Settings()
db_config = DatabaseConfig()

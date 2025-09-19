"""Application settings for the Caching Service.

This module centralizes configuration using Pydantic Settings (v2),
providing typed, environment-driven configuration with sensible defaults.

Environment:
    PROJECT_NAME (str): Human-readable project name. Default: "Caching Service".

Example:
    # .env
    PROJECT_NAME="Caching Service"
"""

from __future__ import annotations

from typing import Iterator

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment."""

    PROJECT_NAME: str = Field(default="Caching Service", env="PROJECT_NAME")

# Module-level singletons
settings = Settings()

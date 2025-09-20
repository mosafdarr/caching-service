"""Shared test bootstrap utilities.

Responsibilities:
    - Adjusts sys.path to ensure project modules are importable in tests.
    - Initializes and exposes a FastAPI TestClient bound to the app.
    - Provides easy access to commonly patched modules/classes.
    - Supplies a `reset_caches()` helper to clear in-memory caches used in tests.

Exports:
    client (TestClient): A test client instance bound to the FastAPI app.
    router_mod: The cache router module for patching cache state.
    CacheController: The controller class used in cache operations.
    caching_utils: Utility module for payload hashing.
    reset_caches (Callable): Clears in-memory cache state between tests.
    MagicMock: For quick mocking of objects in test cases.

Notes:
    - In-memory "redis" caches (REDIS_CACHED_IDS, REDIS_OUTPUT_CACHE) are process-local.
      They must be cleared between tests to prevent state bleed.
    - This module should be imported in test suites rather than redefining these helpers.
"""

import os
import sys

from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Ensure local project directories are on sys.path for import resolution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
LIB_DIR = os.path.join(ROOT_DIR, "libintegration")

for path in (SRC_DIR, ROOT_DIR, LIB_DIR):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

from src.index import app
from libintegration.domain.routers import caches as router_mod
from libintegration.domain.controllers.cache_controller import CacheController
from libintegration.domain.utils import caching_utils

# Shared test client bound to the FastAPI app
client = TestClient(app)


def reset_caches() -> None:
    """Clear in-memory 'redis' stand-ins for test isolation.

    Ensures each test starts with a clean cache state.
    """
    router_mod.REDIS_CACHED_IDS.clear()
    router_mod.REDIS_OUTPUT_CACHE.clear()


__all__ = [
    "client",
    "router_mod",
    "CacheController",
    "caching_utils",
    "reset_caches",
    "MagicMock",
]

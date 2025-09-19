"""Pytest test client configuration.

This module initializes a reusable FastAPI TestClient instance
for running API integration tests against the application.

Attributes:
    client (TestClient): A FastAPI test client bound to the app instance.

Usage:
    from .config import client

    def test_something():
        resp = client.get("/health")
        assert resp.status_code == 200
"""

from fastapi.testclient import TestClient

from src.index import app

# Shared test client for use in unit/integration tests
client = TestClient(app)

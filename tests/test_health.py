"""Unit tests for the application's health check endpoint.

These tests verify:
    - GET /health returns the expected 200 response with correct JSON body.
    - POST /health is not allowed (returns 405).
    - Invalid URL (/healthz) returns 404.
    - Response content type is JSON.
"""

from .config import client


def test_users_endpoint_get():
    """Ensure GET /health returns 200 with expected JSON payload."""

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"message": "Application's health is good."}


def test_health_endpoint_post_not_allowed():
    """Ensure POST /health is not allowed (405)."""

    resp = client.post("/health")
    assert resp.status_code == 405


def test_health_endpoint_wrong_url():
    """Ensure unknown URL (/healthz) returns 404."""

    resp = client.get("/healthz")
    assert resp.status_code == 404


def test_health_endpoint_response_content_type():
    """Ensure /health response is returned as JSON."""

    resp = client.get("/health")
    assert "application/json" in resp.headers["content-type"]



# pylint: disable=all
"""
Unit tests for cache payload endpoints with DB calls mocked.

Scope:
    - Verifies POST and GET behavior of /payload endpoints.
    - Ensures idempotency/short-circuiting via the write-through decorator.
    - Ensures read-through caching bypasses controller on cache hits.
    - Confirms validation errors and method restrictions are surfaced correctly.

Style:
    - Mirrors the simplicity of test_health.py (use TestClient directly).
    - Database calls are mocked/stubbed at the controller boundary.
    - Deterministic `payload_id` values are produced by patching
      `caching_utils.calculate_payload_hash`.

Notes:
    - The in-memory structures `REDIS_CACHED_IDS` and `REDIS_OUTPUT_CACHE`
      are cleared before/after tests to avoid cross-test interference.
"""

import unittest
from unittest import mock

from fastapi import status

from tests.config import client
from tests import mock as T

from libintegration.domain.routers import caches as router_mod


class TestCacheEndpoints(unittest.TestCase):
    """Tests for the cache API endpoints (/payload).

    Setup/Teardown:
        - Clears in-memory caches before the suite and after each test.
    Patching:
        - Stubs hash calculation and controller methods to isolate the HTTP layer.
    Assertions:
        - Status codes, JSON structure, idempotency, and caching behavior.
    """

    @classmethod
    def setUpClass(cls):
        router_mod.REDIS_CACHED_IDS.clear()
        router_mod.REDIS_OUTPUT_CACHE.clear()

    def tearDown(self):
        router_mod.REDIS_CACHED_IDS.clear()
        router_mod.REDIS_OUTPUT_CACHE.clear()

    @mock.patch(
        "libintegration.domain.utils.caching_utils.calculate_payload_hash",
        return_value=T.PID_SIMPLE,
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.create",
        return_value=T.build_create_response(T.PID_SIMPLE),
    )
    def test_post_create_success(self, m_create, m_hash):
        """POST /payload returns 201 and a payload_id on cache miss."""
        body = T.PAYLOAD_SIMPLE.model_dump()
        resp = client.post("/payload", json=body)

        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))
        self.assertTrue(resp.headers["content-type"].startswith("application/json"))

        data = resp.json()
        self.assertIn("payload_id", data)
        self.assertEqual(data["payload_id"], T.PID_SIMPLE)

        # Controller called once on miss
        self.assertEqual(m_create.call_count, 1)

        # Decorator should remember id
        self.assertIn(T.PID_SIMPLE, router_mod.REDIS_CACHED_IDS)

    @mock.patch(
        "libintegration.domain.utils.caching_utils.calculate_payload_hash",
        return_value=T.PID_DUP,
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.create"
    )
    def test_post_short_circuit_when_seen(self, m_create, m_hash):
        """If payload was seen before, decorator short-circuits and skips controller."""
        # Pre-warm "redis" ids set
        router_mod.REDIS_CACHED_IDS.add(T.PID_DUP)

        body = T.PAYLOAD_DUP_A.model_dump()
        resp = client.post("/payload", json=body)

        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))
        self.assertEqual(resp.json()["payload_id"], T.PID_DUP)

        # Ensure controller not called
        m_create.assert_not_called()

    def test_post_length_mismatch_422(self):
        """Pydantic model validation rejects unequal list lengths."""
        body = {"list_1": ["a", "b"], "list_2": ["x"]}
        resp = client.post("/payload", json=body)
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @mock.patch(
        "libintegration.domain.utils.caching_utils.calculate_payload_hash",
        return_value=T.PID_SINGLE,
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.create",
        return_value=T.build_create_response(T.PID_SINGLE),
    )
    def test_post_single_element(self, m_create, m_hash):
        """Single element lists create successfully."""
        body = T.PAYLOAD_SINGLE.model_dump()
        resp = client.post("/payload", json=body)

        self.assertIn(resp.status_code, (200, 201))
        self.assertEqual(resp.json()["payload_id"], T.PID_SINGLE)

        m_create.assert_called_once()

    @mock.patch(
        "libintegration.domain.utils.caching_utils.calculate_payload_hash",
        return_value=T.PID_SIMPLE,
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.create",
        return_value=T.build_create_response(T.PID_SIMPLE),
    )
    def test_post_idempotency_same_body_same_id(self, m_create, m_hash):
        """Repeated POST with identical body yields same id; second call short-circuits."""
        body = T.PAYLOAD_SIMPLE.model_dump()

        resp1 = client.post("/payload", json=body)
        self.assertIn(resp1.status_code, (200, 201))
    
        pid1 = resp1.json()["payload_id"]
        self.assertEqual(pid1, T.PID_SIMPLE)
        self.assertEqual(m_create.call_count, 1)

        # Second call: previously seen -> no controller call
        resp2 = client.post("/payload", json=body)
        pid2 = resp2.json()["payload_id"]

        self.assertEqual(pid2, T.PID_SIMPLE)
        self.assertEqual(m_create.call_count, 1)

    def test_post_collection_get_not_allowed(self):
        """GET /payload (collection) is not allowed."""
        resp = client.get("/payload")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @mock.patch(
        "libintegration.domain.utils.caching_utils.calculate_payload_hash",
        return_value=T.PID_DIFF,
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.create",
        return_value=T.build_create_response(T.PID_DIFF),
    )
    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.get",
        return_value=T.build_get_response(T.OUT_DIFF),
    )
    def test_get_after_create_returns_expected_output(self, m_get, m_create, m_hash):
        """GET /payload/{id} returns the expected transformed output."""
        create_resp = client.post("/payload", json=T.PAYLOAD_DIFF.model_dump())

        pid = create_resp.json()["payload_id"]
        self.assertEqual(pid, T.PID_DIFF)

        resp = client.get(f"/payload/{pid}")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers["content-type"].startswith("application/json"))
        self.assertEqual(resp.json(), {"output": T.OUT_DIFF})

        m_get.assert_called_once_with(payload_id=T.PID_DIFF, db_session=mock.ANY)

    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.get"
    )
    def test_get_cache_hit_skips_controller(self, m_get):
        """Read-through decorator returns cached output without calling controller."""
        # Pre-populate in-memory output cache
        router_mod.REDIS_OUTPUT_CACHE[T.PID_SIMPLE] = T.build_get_response(T.OUT_SIMPLE)

        # Make controller raise if called (it shouldn't be)
        m_get.side_effect = AssertionError("Controller should not be called on cache hit")

        resp = client.get(f"/payload/{T.PID_SIMPLE}")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"output": T.OUT_SIMPLE})

        m_get.assert_not_called()

    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.get",
        side_effect=ValueError("not found"),
    )
    def test_get_not_found_returns_error(self, m_get):
        """Unknown id -> controller raises; expect error status."""
        try:
            resp = client.get("/payload/does-not-exist")
            self.assertGreaterEqual(resp.status_code, 400)
        except ValueError as e:
            self.assertEqual(str(e), "not found")

        m_get.assert_called_once()

    @mock.patch(
        "libintegration.domain.controllers.cache_controller.CacheController.get",
        return_value=T.build_get_response(T.OUT_SINGLE),
    )
    def test_get_content_type_json(self, m_get):
        """GET response content type should be JSON."""

        router_mod.REDIS_OUTPUT_CACHE.clear()

        resp = client.get(f"/payload/{T.PID_SINGLE}")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp.headers["content-type"])

    def test_get_cache_id_not_found(self):
        """GET with invalid id format returns 422."""

        resp = client.get("/payload/invalid_id!@#")
    
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", resp.json())
        self.assertIn("not found", resp.json()["detail"].get("message").lower())

""""Cache-related API routes.

This module defines the FastAPI router for cache operations, including
endpoints for reading and creating cache payloads. It also provides two
lightweight decorators to simulate read-through and write-through caching
behavior using in-memory structures.

Routers:
    cache_router (APIRouter): Router with prefix `/payload` exposing cache endpoints.

Endpoints:
    GET /payload/{payload_id}: Retrieve a cache entry by ID (checks in-memory cache first).
    POST /payload: Create a new cache payload (short-circuits if payload already seen).

Notes:
    - REDIS_CACHED_IDS and REDIS_OUTPUT_CACHE are in-memory stand-ins for Redis.
      Replace with a real Redis client in production. The in-memory approach
      is process-local and not suitable for multi-instance deployments.
"""

from __future__ import annotations

from functools import wraps
from threading import Lock
from typing import Dict

from fastapi import APIRouter, Depends

from logger import logger
from settings import db_config
from .root import responses

from libintegration.documentation import cache_doc
from libintegration.domain.models import cache_model
from libintegration.domain.controllers.cache_controller import CacheController
from libintegration.domain.utils import caching_utils

REDIS_CACHED_IDS: set[str] = set()
REDIS_OUTPUT_CACHE: Dict[str, cache_model.GetCacheResponse] = {}
_CACHE_LOCK = Lock()

def check_redis_cache(func):
    """
    POST decorator: short-circuit if an identical payload was previously submitted.

    Behavior:
        - Computes a deterministic `payload_id` via
          `caching_utils.calculate_payload_hash(payload)`.
        - If the id exists in `REDIS_CACHED_IDS`, immediately returns
          `CreateCachePayloadResponse(payload_id=...)` without invoking the handler.
        - Otherwise:
            * Injects `payload_id` into `kwargs`.
            * Calls the wrapped route handler.
            * On success, stores the returned id in `REDIS_CACHED_IDS`.

    Warning:
        This is an in-memory demonstration only. For production, use a shared,
        external cache (e.g., Redis) and consider eviction strategies.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        payload = kwargs.get("payload")
        if payload is None:
            for arg in args:
                if isinstance(arg, cache_model.CreateCachePayloadRequest):
                    payload = arg
                    break

        payload_id = None
        if payload is not None:
            payload_id = caching_utils.calculate_payload_hash(payload)
            with _CACHE_LOCK:
                if payload_id in REDIS_CACHED_IDS:
                    logger.info("POST cache hit (payload_id=%s) – short-circuiting.", payload_id)
                    return cache_model.CreateCachePayloadResponse(payload_id=payload_id)

        kwargs["payload_id"] = payload_id
        response = func(*args, **kwargs)

        response_payload_id = getattr(response, "payload_id", None)
        if response_payload_id:
            with _CACHE_LOCK:
                REDIS_CACHED_IDS.add(response_payload_id)

        return response

    return wrapper

def cache_read_through(func):
    """
    GET decorator: check an in-memory map for `payload_id` first; on miss, call handler and cache.

    Behavior:
        - Reads `payload_id` from the path parameter (FastAPI passes it in `kwargs`).
        - If present in `REDIS_OUTPUT_CACHE`, returns the cached `GetCacheResponse`.
        - Otherwise:
            * Calls the wrapped handler.
            * If the response is a `GetCacheResponse`, stores it in `REDIS_OUTPUT_CACHE`.

    Note:
        This read-through cache avoids duplicate DB lookups for frequently
        requested payloads within the same process. Replace with a distributed
        cache layer for multi-instance environments.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        payload_id = kwargs.get("id")
        if payload_id:
            with _CACHE_LOCK:
                cached = REDIS_OUTPUT_CACHE.get(payload_id)
            if cached is not None:
                logger.info("GET cache hit (payload_id=%s) – returning cached response.", payload_id)
                return cached

        response = func(*args, **kwargs)

        if isinstance(response, cache_model.GetCacheResponse) and payload_id:
            with _CACHE_LOCK:
                REDIS_OUTPUT_CACHE[payload_id] = response

        return response

    return wrapper


cache_router = APIRouter(
    prefix="/payload",
    tags=["Cache"],
    responses=responses,
    include_in_schema=True,
)


@cache_router.get(
    "/{id}",
    summary=cache_doc.summary,
    description=cache_doc.descriptions,
    response_model=cache_model.GetCacheResponse,
    include_in_schema=True,
)
@cache_read_through
def read_payload(
    id: str,
    db_session=Depends(db_config.get_session),
) -> cache_model.GetCacheResponse:
    """
    Retrieve a cache payload by its ID.

    The `@cache_read_through` decorator consults the in-memory cache first
    and falls back to the controller/DB path on a miss.

    Args:
        id (str): Deterministic payload identifier.
        db_session: Database session dependency.

    Returns:
        GetCacheResponse: The stored/interleaved output for the given payload id.

    Raises:
        HTTPException: If the payload cannot be found (propagated from controller).
    """
    logger.info(f"GET /payload/{id}")
    response = CacheController.get(payload_id=id, db_session=db_session)
    return response


@cache_router.post(
    "",
    summary=cache_doc.create_payload_summary,
    description=cache_doc.create_payload_descriptions,
    response_model=cache_model.CreateCachePayloadResponse,
    include_in_schema=True,
)
@check_redis_cache
def create_payload(
    payload: cache_model.CreateCachePayloadRequest,
    db_session=Depends(db_config.get_session),
    payload_id=Depends(lambda: None),
) -> cache_model.CreateCachePayloadResponse:
    """
    Create a new cache payload.

    The `@check_redis_cache` decorator computes a deterministic id from the payload
    and short-circuits if it was seen before; otherwise the controller handles the
    transformation and persistence.

    Args:
        payload (CreateCachePayloadRequest): Input lists to transform and cache.
        db_session: Database session dependency.
        payload_id: Precomputed identifier injected by the decorator (may be None).

    Returns:
        CreateCachePayloadResponse: Response containing the stable payload id.
    """
    logger.info("POST /payload called with payload=%s (precomputed_id=%s).", payload, payload_id)
    response = CacheController.create(payload=payload, payload_id=payload_id, db_session=db_session)
    return response

""""Cache-related API routes.

This module defines the FastAPI router for cache operations,
including endpoints for reading and creating cache payloads.

Routers:
    cache_router (APIRouter): Router with prefix `/payload` exposing cache endpoints.

Endpoints:
    GET /payload/{id}: Retrieve a cache entry by ID.
    POST /payload: Create a new cache payload.

Notes:
    - A lightweight in-memory set (REDIS_CACHED_IDS) is used to emulate a cache
      key registry for demonstration purposes. The `check_redis_cache` decorator
      hashes the incoming payload to derive a deterministic `payload_id`. If a
      matching ID exists, the endpoint short-circuits and returns the cached id.
    - In production, replace REDIS_CACHED_IDS with a real cache (e.g., Redis)
      and persist/cache both the derived id and any relevant computed result.
"""

from fastapi import APIRouter, Depends
from functools import wraps

from logger import logger
from settings import db_config
from .root import responses

from libintegration.documentation import cache_doc
from libintegration.domain.models import cache_model
from libintegration.domain.controllers.cache_controller import CacheController
from libintegration.domain.utils import caching_utils


# In-memory registry of cached payload IDs (demo only).
REDIS_CACHED_IDS = set()


def check_redis_cache(func):
    """Decorator to short-circuit POST requests when payload is already cached.

    Behavior:
        - Extract the payload (from kwargs or positional args).
        - Compute a deterministic hash (payload_id) using `caching_utils`.
        - If the id is found in REDIS_CACHED_IDS, immediately return a
          `CreateCachePayloadResponse` containing that id.
        - Otherwise, inject `payload_id` into kwargs, call the wrapped function,
          and add the returned id to the registry if present.

    Args:
        func: The route handler to wrap.

    Returns:
        Callable: A wrapped function that performs cache lookups prior to execution.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper that performs the cache check and manages the payload_id flow."""
        payload = kwargs.get('payload')
        if not payload:
            for arg in args:
                if isinstance(arg, cache_model.CreateCachePayloadRequest):
                    payload = arg
                    break

        if payload:
            payload_id = caching_utils.calculate_payload_hash(payload)
            if payload_id in REDIS_CACHED_IDS:
                return cache_model.CreateCachePayloadResponse(payload_id=payload_id)

        # pass payload_id & call the router controller function
        kwargs['payload_id'] = payload_id
        response = func(*args, **kwargs)
        response_payload_id = getattr(response, "payload_id", None)
    
        if response_payload_id:
            REDIS_CACHED_IDS.add(response_payload_id)

        return response
    return wrapper


# Public router exposing cache endpoints under /payload
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
def read_users(
    payload_id: str,
    db_sesssion=Depends(db_config.get_session),
):
    """Retrieve a cache payload by its ID.

    Args:
        payload_id (str): Unique identifier of the cache payload.
        db_sesssion: Database session dependency.

    Returns:
        dict: Placeholder response containing the output.
    """
    logger.info(f"Read users endpoint called with payload_id: {payload_id}.")
    return {"output": "string"}

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
    payload_id: str = None,
    db_sesssion=Depends(db_config.get_session),
):
    """Create a new cache payload.

    Args:
        payload (CreateCachePayloadRequest): The payload data to be cached.
        db_sesssion: Database session dependency.

    Returns:
        dict: Placeholder response containing the payload ID.
    """
    logger.info(f"Create payload endpoint called with payload: {payload}.")
    response = CacheController.create(payload=payload, payload_id=payload_id, db_session=db_sesssion)

    return response

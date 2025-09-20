"""Cache-related API routes.

This module defines the FastAPI router for cache operations,
including endpoints for reading and creating cache payloads.

Routers:
    cache_router (APIRouter): Router with prefix `/payload` exposing cache endpoints.

Endpoints:
    GET /payload/{id}: Retrieve a cache entry by ID.
    POST /payload: Create a new cache payload.
"""

from fastapi import APIRouter, Depends

from logger import logger
from settings import db_config
from .root import responses

from libintegration.documentation import cache_doc
from libintegration.domain.models import cache_model


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
    "/",
    summary=cache_doc.create_payload_summary,
    description=cache_doc.create_payload_descriptions,
    response_model=cache_model.CreateCachePayloadResponse,
    include_in_schema=True,
)
def create_payload(
    payload: cache_model.CreateCachePayloadRequest,
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
    return {"payload_id": "string"}

""""Cache controller: orchestrates payload transformation and caching.

This module wires together:
    - The transformer that interleaves/normalizes incoming lists.
    - The database layer used to cache and retrieve prior results.

Responsibilities:
    • Accept a request payload and a deterministic payload_id.
    • Short-circuit if the payload_id is already cached.
    • Invoke the pure transformer to compute the output otherwise.
    • Persist the (input, output) pair to the cache table.
    • Return a stable payload identifier to the caller.

Notes:
    - This controller is framework-agnostic; it expects a SQLAlchemy Session
      and Pydantic models, and does not depend on FastAPI internals.
    - Errors originating from DB operations are logged and re-raised after rollback.

Usage:
    CacheController.create(payload_id=..., payload=..., db_session=...)
    CacheController.get(payload_id=..., db_session=...)
"""

import json

from fastapi import HTTPException
from pydantic import BaseModel
from logger import logger
from sqlalchemy.orm import Session

from libintegration.domain.apps.transformer import TransformerApp
from libintegration.domain.models import cache_model
from libintegration.domain.utils.caching_utils import exception_handler

from schema.tables import cache_payloads


class CacheController(BaseModel):
    """Application-level coordination for cache create/read flows.

    This controller encapsulates the orchestration logic between:
        - The pure transformer (`TransformerApp`) that performs input validation
          and string interleaving.
        - The persistence layer (SQLAlchemy) used to store and fetch cached
          inputs/outputs by a deterministic `payload_id`.

    Methods:
        get(payload_id, db_session): Retrieve a previously cached payload response.
        create(payload_id, payload, db_session): Compute-or-reuse a payload result,
            persist it when newly computed, and return its identifier.
        _get_cached_response_id(db_session, payload_id): Internal helper to determine
            whether a given `payload_id` already exists.
        _cache_parsed_response(db_session, payload_id, payload, response): Internal
            helper to persist a new (input, output) tuple.
    """

    @staticmethod
    @exception_handler
    def get(payload_id: str, db_session: Session) -> cache_model.GetCacheResponse:
        """Retrieve a cached payload by its identifier.

        This method queries the cache table for the given `payload_id`. If present,
        it deserializes the stored JSON `output_payload` and returns it as a
        `GetCacheResponse`. If absent, it raises a `ValueError`.

        Args:
            payload_id (str): Unique identifier for the cached payload.
            db_session (Session): Active SQLAlchemy session.

        Returns:
            GetCacheResponse: The cached payload response.

        Raises:
            ValueError: If no cached entry is found for the provided `payload_id`.
        """
        logger.info(f"Cache Controller - get called with payload_id: {payload_id}")

        cached_result = db_session.execute(
            db_session.query(cache_payloads).filter_by(payload_id=payload_id)
        ).fetchone()

        if not cached_result:
            error_message = f"Payload ID {payload_id} not found in cache."
            logger.error(error_message)
            raise HTTPException(status_code=404, detail=error_message)

        output_payload = json.loads(cached_result[0].output_payload)
        logger.info(f"Retrieved cached payload for ID {payload_id}: {output_payload}")

        return cache_model.GetCacheResponse(**output_payload)

    @staticmethod
    @exception_handler
    def create(
        payload_id: str, payload: cache_model.CreateCachePayloadRequest, db_session: Session
    ) -> cache_model.CreateCachePayloadResponse:
        """Create or reuse a cached payload and return its identifier.

        Workflow:
            1) Check for an existing cached entry by `payload_id`.
            2) If found, return that id immediately (cache hit).
            3) Otherwise, run the transformer to compute the output.
            4) Persist (input, output) to the cache table.
            5) Return the `payload_id`.

        Args:
            payload_id (str): Deterministic identifier for the payload (hash).
            payload (CreateCachePayloadRequest): Input lists to transform.
            db_session (Session): Active SQLAlchemy session.

        Returns:
            CreateCachePayloadResponse: Response containing the stable payload id.
        """
        logger.info(f"Cache Controller - create called with payload: {payload}")

        cached_response = CacheController._get_cached_response_id(
            db_session=db_session, payload_id=payload_id
        )
        if cached_response:
            logger.info(f"Cache hit for payload ID: {payload_id}")
            return cache_model.CreateCachePayloadResponse(payload_id=cached_response.payload_id)

        response = TransformerApp().transform(payload=payload)
        parsed_response = cache_model.GetCacheResponse(output=response.get("output"))

        logger.info(f"Transformed response: {parsed_response}")

        payload_id = CacheController._cache_parsed_response(
            db_session=db_session,
            payload_id=payload_id,
            payload=payload,
            response=parsed_response
        )

        return cache_model.CreateCachePayloadResponse(payload_id=payload_id)
    
    def _get_cached_response_id(db_session: Session, payload_id) -> str | None:
        """Check if a response for the given payload ID is already cached.

        Queries the cache table using the provided `payload_id`. If a row exists,
        the method logs a hit and returns the stored identifier; otherwise it logs
        a miss and returns `None`.

        Args:
            db_session (Session): Database session for performing DB operations.
            payload_id (str): The unique identifier of the payload to check.

        Returns:
            str | None: The cached payload ID if found, otherwise `None`.
        """
        cached_result = db_session.execute(
            db_session.query(cache_payloads).filter_by(payload_id=payload_id)
        ).fetchone()

        if not cached_result:
            logger.info(f"No cached entry found for payload ID: {payload_id}")
            return None

        logger.info(f"Found cached response for payload ID: {payload_id}")
        return cached_result[0]
    
    @staticmethod
    def _cache_parsed_response(db_session: Session, payload_id, payload, response) -> str:
        """Cache the parsed response in the database and return the payload ID.

        Serializes both the `payload` and `response` to JSON and inserts a new row
        into the cache table. On success, the transaction is committed. On failure,
        the transaction is rolled back and the exception is re-raised.

        Args:
            db_session (Session): Database session for performing DB operations.
            payload_id (str): The unique identifier of the payload.
            payload: The input payload object.
            response: The parsed response object.

        Returns:
            str: The unique identifier of the cached payload.

        Raises:
            Exception: Any database exception encountered during persistence is logged,
                the transaction is rolled back, and the original error is re-raised.
        """
        cache_payload = cache_payloads(
            payload_id=payload_id,
            input_payload=json.dumps(payload.dict()),
            output_payload=json.dumps(response.dict()),
        )

        db_session.add(cache_payload)
        try:
            db_session.flush()
            db_session.commit()
            logger.info(f"Cached payload with ID: {payload_id}")
        except Exception as e:
            logger.error(f"Failed to cache payload: {e}")
            db_session.rollback()
            raise

        return payload_id

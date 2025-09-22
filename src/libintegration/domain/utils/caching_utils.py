import hashlib
import json

from fastapi import HTTPException
from functools import wraps
from pydantic import ValidationError
from logger import logger

def calculate_payload_hash(payload: dict) -> str:
    """Calculate a unique hash for the given payload.

    Args:
        payload (CreateCachePayloadRequest): The input payload to hash.
    Returns:
        str: A unique hash string representing the payload.
    """

    payload_str = json.dumps(payload.dict(), sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()

def exception_handler(func):
    """Decorator to handle exceptions and log errors.

    Args:
        func (Callable): The function to wrap.
    Returns:
        Callable: The wrapped function with exception handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as error:
            raise HTTPException(
                status_code=error.status_code,
                detail={"message": error.detail}
            )from error
        except ValidationError as error:
            logger.error(f"Validation Error in {func.__name__}: {error}")
            raise HTTPException(status_code=422, detail={"message": str(error)}) from error
        except ValueError as error:
            logger.error(f"Value Error in {func.__name__}: {error}")
            raise HTTPException(status_code=400, detail={"message": str(error)}) from error
        except Exception as error:
            logger.error(f"Unexpected Error in {func.__name__}: {error}")
            raise HTTPException(status_code=500, detail={"message": "Internal Server Error"}) from error

    return wrapper
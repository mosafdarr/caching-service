import hashlib
import json

def calculate_payload_hash(payload: dict) -> str:
    """Calculate a unique hash for the given payload.

    Args:
        payload (CreateCachePayloadRequest): The input payload to hash.
    Returns:
        str: A unique hash string representing the payload.
    """

    payload_str = json.dumps(payload.dict(), sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()

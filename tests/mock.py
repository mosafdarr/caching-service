"""
Centralized mock payloads and response builders for cache tests.

This module provides canonical payloads and deterministic payload IDs for use in
unit tests, as well as helper functions to build mock response objects.
"""

from libintegration.domain.models.cache_model import (
    CreateCachePayloadRequest,
    CreateCachePayloadResponse,
    GetCacheResponse,
)

#: A payload with multiple strings in both lists.
PAYLOAD_SIMPLE = CreateCachePayloadRequest(
    list_1=["first string", "second string", "third string"],
    list_2=["other string", "another string", "last string"],
)

#: A payload with a single string in each list.
PAYLOAD_SINGLE = CreateCachePayloadRequest(
    list_1=["hello"],
    list_2=["world"],
)

#: A payload for duplicate test A.
PAYLOAD_DUP_A = CreateCachePayloadRequest(
    list_1=["cache", "hit"],
    list_2=["test", "again"],
)

#: A payload for duplicate test B (identical to A).
PAYLOAD_DUP_B_SAME_AS_A = CreateCachePayloadRequest(
    list_1=["cache", "hit"],
    list_2=["test", "again"],
)

#: A payload with different values.
PAYLOAD_DIFF = CreateCachePayloadRequest(
    list_1=["foo", "bar", "baz"],
    list_2=["alpha", "beta", "gamma"],
)

# Deterministic payload IDs (for monkeypatching hash)

PID_SIMPLE = "pid_simple_123"
PID_SINGLE = "pid_single_456"
PID_DUP = "pid_dup_999"
PID_DIFF = "pid_diff_777"

# Response builders

def build_create_response(pid: str) -> CreateCachePayloadResponse:
    """
    Build a CreateCachePayloadResponse with the given payload ID.

    Args:
        pid (str): The payload ID.

    Returns:
        CreateCachePayloadResponse: The response object.
    """
    return CreateCachePayloadResponse(payload_id=pid)


def build_get_response(output: str) -> GetCacheResponse:
    """
    Build a GetCacheResponse with the given output string.

    Args:
        output (str): The output string.

    Returns:
        GetCacheResponse: The response object.
    """
    return GetCacheResponse(output=output)

# Expected Output Responses

#: Expected output for PAYLOAD_SIMPLE (uppercased & interleaved).
OUT_SIMPLE = (
    "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
)

#: Expected output for PAYLOAD_SINGLE.
OUT_SINGLE = "HELLO, WORLD"

#: Expected output for PAYLOAD_DIFF.
OUT_DIFF = "FOO, ALPHA, BAR, BETA, BAZ, GAMMA"

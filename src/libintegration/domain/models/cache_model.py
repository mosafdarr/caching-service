"""Pydantic models for cache payload API.

This module defines request and response models for cache payload
operations, including validation rules and example payloads.

Classes:
    CreateCachePayloadRequest: Request body schema for creating a cache payload.
    CreateCachePayloadResponse: Response schema after creating a cache payload.
    GetCacheResponse: Response schema when retrieving a cache payload.
"""

from pydantic import BaseModel, Field, model_validator


class CreateCachePayloadRequest(BaseModel):
    """Request model for creating a cache payload.

    Attributes:
        list_1 (list[str]): First list of strings.
        list_2 (list[str]): Second list of strings (must be the same length as list_1).

    Validation:
        Ensures that `list_1` and `list_2` are provided and of equal length.
    """

    list_1: list[str] = Field(..., description="First list of strings")
    list_2: list[str] = Field(
        ..., description="Second list of strings (same length as list_1)"
    )

    @model_validator(mode="after")
    def check_lists_length(self):
        """Validate that both lists have the same length."""
        if (
            self.list_1 is not None
            and self.list_2 is not None
            and len(self.list_1) != len(self.list_2)
        ):
            raise ValueError("list_1 and list_2 must be of the same length")
        return self

    class Config:
        """Pydantic configuration with example payloads."""

        examples = {
            "default": {
                "summary": "A typical request",
                "value": {"list_1": ["a", "b", "c"], "list_2": ["1", "2", "3"]},
            }
        }


class CreateCachePayloadResponse(BaseModel):
    """Response model after creating a cache payload.

    Attributes:
        payload_id (str): Unique identifier for the generated payload.
    """

    payload_id: str = Field(
        ..., description="Unique identifier for the generated payload"
    )

    class Config:
        """Pydantic configuration with example payloads."""

        examples = {
            "default": {
                "summary": "A typical response",
                "value": {"payload_id": "abc123"},
            }
        }


class GetCacheResponse(BaseModel):
    """Response model when retrieving a cache payload.

    Attributes:
        output (str): Final interleaved output string.
    """

    output: str = Field(..., description="Generated interleaved payload string")

    class Config:
        """Pydantic configuration with example payloads."""

        examples = {
            "default": {
                "summary": "A typical get response",
                "value": {"output": "a1b2c3"},
            }
        }

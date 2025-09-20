"""Error response models for API integration.

This module defines Pydantic models used for standardized error
responses across the application.

Classes:
    ErrorModelDetail: Represents a single error detail with code, message, and object.
    IntegrationErrorModel: Wrapper model containing an error detail object.
"""

from pydantic import Field, BaseModel


class ErrorModelDetail(BaseModel):
    """Represents a single error detail in API responses.

    Attributes:
        code (str): Application-specific error code.
        message (str): Human-readable error message.
        object (str): The object or field associated with the error.
    """

    code: str = Field(None, description="Error code")
    message: str = Field(None, description="Error message")
    object: str = Field(None, description="Error object")


class IntegrationErrorModel(BaseModel):
    """Wrapper model for standardized error responses.

    Attributes:
        details (ErrorModelDetail): The error details object containing
            code, message, and object information.
    """

    details: ErrorModelDetail = Field(None, description="Error details")

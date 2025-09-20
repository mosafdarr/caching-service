"""Standardized API error response mappings.

This module defines reusable error response configurations for FastAPI routes,
ensuring consistent error handling and schema usage across the application.

Attributes:
    responses (dict): A dictionary of common HTTP error codes mapped to
        `IntegrationErrorModel` with descriptive messages.

Usage:
    from libintegration.api.responses import responses

    @router.get("/items", responses=responses)
    async def get_items():
        ...
"""

from libintegration.domain.models.error_model import IntegrationErrorModel


responses = {
    400: {"model": IntegrationErrorModel, "description": "Bad Request"},
    401: {"model": IntegrationErrorModel, "description": "Unauthorized"},
    403: {"model": IntegrationErrorModel, "description": "Forbidden"},
    404: {"model": IntegrationErrorModel, "description": "Not Found"},
    422: {"model": IntegrationErrorModel, "description": "Unprocessable Entity"},
    429: {"model": IntegrationErrorModel, "description": "Too Many Requests"},
    500: {"model": IntegrationErrorModel, "description": "Internal Server Error"},
    501: {"model": IntegrationErrorModel, "description": "Not Implemented"},
}

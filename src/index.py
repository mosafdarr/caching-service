"""Main application entry point for the Caching Service.

This module initializes the FastAPI application, wires up middleware,
and exposes a minimal health-check endpoint for runtime monitoring.

Attributes:
    app (FastAPI): The FastAPI application instance.

Endpoints:
    GET /health: Returns a simple health status payload.

Example:
    Run with uvicorn (dev):
        uvicorn src.index:app --reload
"""

from fastapi import FastAPI
from logger import logger
from settings import settings

from libintegration.middlewares.header_middleware import HeaderMiddleware


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A caching service for efficient data retrieval and storage.",
    version="0.1.0",
)

# Register cross-cutting middleware (CORS, timing, global error handling).
HeaderMiddleware.add_middleware(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict[str, str]: A short message indicating the application health.
    """
    logger.info("Health check endpoint called.")
    return {"message": "Application's health is good."}

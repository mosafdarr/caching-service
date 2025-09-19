"""Header and exception middleware for FastAPI applications.

This module provides middleware setup to handle:
    - Cross-Origin Resource Sharing (CORS)
    - Adding a custom process time header to each response
    - A global exception handler that returns a standard error response

Classes:
    HeaderMiddleware: Provides a static method to attach middleware to a FastAPI app.

Example:
    from fastapi import FastAPI
    from libintegration.middlewares.header_middleware import HeaderMiddleware

    app = FastAPI()
    HeaderMiddleware.add_middleware(app)
"""

from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


class HeaderMiddleware:
    """Namespace for registering application-wide HTTP middleware."""

    @staticmethod
    def add_middleware(app: FastAPI):
        """Attach middleware and exception handlers to the FastAPI app.

        Args:
            app (FastAPI): The FastAPI application instance to which middleware is added.
        """
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            """Middleware to append a process time header to responses.

            Args:
                request (Request): The incoming HTTP request.
                call_next (Callable): The next middleware or endpoint handler.

            Returns:
                Response: The processed HTTP response with an added header.
            """
            response = await call_next(request)
            response.headers["X-Process-Time"] = "Processed in {time} seconds".format(time=0.0)

            return response

        @app.exception_handler(Exception)
        async def exception_handler(request: Request, exc: Exception):
            """Global exception handler for unhandled errors.

            Args:
                request (Request): The request that triggered the exception.
                exc (Exception): The exception raised.

            Returns:
                JSONResponse: A JSON response with a 500 status code.
            """
            return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

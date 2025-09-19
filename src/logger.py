import logging
import sys

from loguru import logger


def setup_logging() -> None:
    """
    Configure simple and consistent logging for the app.
    - INFO level by default
    - Outputs to stdout
    - Human-readable format with timestamp, level, and message
    """

    # Remove default loguru handlers
    logger.remove()

    # Add a simple format
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
    )

    # Redirect standard logging to loguru (so FastAPI/Uvicorn logs match)
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            logger.log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

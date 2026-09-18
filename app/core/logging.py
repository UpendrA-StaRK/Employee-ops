"""Minimal application logging configuration.

Establishes a foundation that can be extended with structured logging
(e.g. structlog, JSON formatting) in later weeks.
"""
import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logger for the application.

    Called once at application startup from main.py.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Reduce noise from third-party libraries in development.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
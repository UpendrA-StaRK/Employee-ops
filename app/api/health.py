"""Health check router.

GET /health - returns service status.
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str


@router.get("/health", response_model=HealthResponse, tags=["operations"])
def health_check() -> HealthResponse:
    """Return service health status."""
    from app.core.config import settings
    from app.db.session import check_db_connection

    db_status = "ok" if check_db_connection() else "unavailable"

    logger.debug("Health check called - db_status=%s", db_status)

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        database=db_status,
    )
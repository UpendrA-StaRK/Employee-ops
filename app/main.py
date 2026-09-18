"""FastAPI application entry point."""
import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Employee Operations AI Case Management Platform - "
        "Week 1: Project Foundation"
    ),
)

from app.api.health import router as health_router  # noqa: E402
from app.api.employee import router as employee_router  # noqa: E402

app.include_router(health_router)
app.include_router(employee_router)

logger.info(
    "Application started | env=%s | version=%s",
    settings.app_env,
    settings.app_version,
)
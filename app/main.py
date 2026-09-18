"""FastAPI application entry point."""
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.health import router as health_router
from app.api.employee import router as employee_router
from app.api.case import router as case_router

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Employee Operations AI Case Management Platform — "
        "Week 1: Foundation, Employee & Case Management"
    ),
)


# ---------------------------------------------------------------------------
# Middleware: lightweight correlation/request ID
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a unique request_id to every request for log correlation."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(employee_router)
app.include_router(case_router)

logger.info(
    "Application started | env=%s | version=%s",
    settings.app_env,
    settings.app_version,
)
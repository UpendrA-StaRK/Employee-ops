# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.9.18 AS uv

FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/
RUN apt-get update \
    && apt-get install --yes --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appgroup \
    && useradd --system --gid appgroup --create-home appuser

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

COPY --chown=appuser:appgroup pyproject.toml uv.lock ./
USER appuser
RUN uv sync --frozen --extra dev --no-install-project

COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup generators ./generators
COPY --chown=appuser:appgroup tests ./tests

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000"]

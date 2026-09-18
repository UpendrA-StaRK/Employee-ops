# Employee Operations AI Case Management Platform

An AI-powered employee operations case management system built incrementally
across a five-week curriculum. This is **Week 1: Project Foundation**.

---

## Purpose

The system will allow employees and HR/operations teams to raise, manage, track,
and resolve employee-operation cases (leave, onboarding, policy queries, HR
requests). AI capabilities will assist with case understanding, policy retrieval,
response generation, and case resolution.

This week establishes the backend project structure, tooling, configuration,
database preparation, and a minimal running FastAPI service.

---

## Five-Week Roadmap

| Week | Focus |
|------|-------|
| 1    | **Project foundation** (this week) |
| 2    | Data ingestion, quality, and pipelines |
| 3    | RAG / policy knowledge assistant |
| 4    | AI workflows, tools, approvals, security, observability |
| 5    | Full FDE integration, hardening, and deployment |

> **Note:** AI, RAG, vector databases, authentication, and integrations are
> intentionally NOT implemented yet. They will be added in later weeks.

---

## Technology Stack

| Layer       | Technology |
|-------------|------------|
| Language    | Python 3.12+ |
| Package mgr | uv |
| Web API     | FastAPI + Uvicorn |
| Validation  | Pydantic v2 |
| ORM         | SQLAlchemy 2.x |
| Migrations  | Alembic |
| Database    | PostgreSQL (psycopg2 / asyncpg) |
| Testing     | pytest |

---

## Local Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- PostgreSQL running locally (optional for Week 1 — the app starts without it)

### Install dependencies

```bash
# Create virtual environment and install runtime + dev dependencies
uv sync --extra dev
```

### Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

---

## Running the Application

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

Interactive API docs: http://localhost:8000/docs

---

## Running Tests

```bash
uv run pytest
```

To run only API tests:

```bash
uv run pytest tests/api/
```

To run only unit tests:

```bash
uv run pytest tests/unit/
```

---

## Health Endpoint

```
GET /health
```

**Response (200 OK):**

```json
{
  "status": "ok",
  "service": "Employee Operations AI",
  "version": "0.1.0",
  "database": "ok"
}
```

The `database` field is `"ok"` when PostgreSQL is reachable, `"unavailable"` otherwise.
The endpoint always returns HTTP 200 — database unavailability is reported in the body, not via status code.

---

## Current Limitations (Week 1)

- No employee or case data models yet.
- No authentication or authorization.
- No business logic or CRUD operations.
- No AI, RAG, or LLM integrations.
- No data ingestion or generation pipelines.
- No frontend.
- Database schema migrations (Alembic) are prepared but no migrations exist yet.
- PostgreSQL is required from Week 2 onwards; Week 1 works without an active database connection.

# Employee Operations AI Case Management Platform

An AI-powered employee operations case management system built incrementally
across a five-week curriculum. **Week 1: Project Foundation + Case Management.**

---

## Purpose

Allow employees and HR/operations teams to raise, manage, track, and resolve
employee-operation cases (leave, payroll, access, benefits, general queries).
AI capabilities will be added in later weeks to assist with case understanding,
policy retrieval, and case resolution.

---

## Five-Week Roadmap

| Week | Focus |
|------|-------|
| 1    | **Project foundation + Case Management** (this week) |
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
| Database    | PostgreSQL (psycopg3 / psycopg[binary]) |
| Testing     | pytest + pytest-cov |

---

## Local Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- PostgreSQL running locally

### Install dependencies

```bash
uv sync --extra dev
```

### Configure environment

```bash
cp .env.example .env
# Edit .env and set DATABASE_URL to your PostgreSQL connection string
```

Required variables:

| Variable       | Description |
|----------------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:port/dbname` |
| `APP_ENV`      | `development` \| `production` |
| `LOG_LEVEL`    | `DEBUG` \| `INFO` \| `WARNING` |

### Create the database

```sql
-- In psql:
CREATE DATABASE employee_ops;
CREATE DATABASE employee_ops_test;  -- for running tests
```

### Run migrations

```bash
uv run alembic upgrade head
```

### Start the application

```bash
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

---

## Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=term-missing

# Only unit tests (no database needed)
uv run pytest tests/unit/

# Only API/integration tests
uv run pytest tests/api/
```

### Test database approach

Tests run against a **separate `employee_ops_test` database** (derived
automatically by appending `_test` to your `DATABASE_URL`).

Each test gets a **rolled-back transaction** — changes are never committed to
disk and tests are fully isolated and order-independent.  

Override the test database URL by setting `TEST_DATABASE_URL` in `.env`.

---

## Architecture

```
HTTP Request
    │
FastAPI Router (app/api/)      ← thin: routing, schema, HTTP codes
    │
Service (app/services/)        ← business logic, transition rules, commit
    │
Repository (app/repositories/) ← database access only, flush not commit
    │
SQLAlchemy ORM (app/models/)
    │
PostgreSQL
```

**Pattern:** Repositories only `flush()`. Services own `db.commit()`.
This means multi-step operations (case update + history record) are
committed atomically in a single transaction.

---

## API Endpoints

### Operations
- `GET /health` — Service health (always 200; DB status in body)

### Employees
- `POST /employees` — Create a new employee
- `GET /employees/{employee_id}` — Retrieve an employee by ID

### Cases
- `POST /cases` — Create a case (always starts `OPEN`; writes initial history)
- `GET /cases` — List cases with optional filters (`employee_id`, `status`, `category`, `priority`)
- `GET /cases/{case_id}` — Retrieve a case by ID
- `PATCH /cases/{case_id}` — Update a case (validates lifecycle rules on status change)
- `GET /cases/{case_id}/history` — Status history in chronological order

---

## Case Lifecycle

Every case starts `OPEN`. Status transitions are strictly validated.

```
OPEN ──────────────────────────────────────────── CLOSED
  │                                                  ▲
  └──► IN_PROGRESS ──► PENDING ──► RESOLVED ────────┘
             ▲             │            │
             └─────────────┘            └──► IN_PROGRESS  (re-open)
```

| From          | To                            |
|---------------|-------------------------------|
| `OPEN`        | `IN_PROGRESS`, `CLOSED`       |
| `IN_PROGRESS` | `PENDING`, `RESOLVED`         |
| `PENDING`     | `IN_PROGRESS`, `RESOLVED`     |
| `RESOLVED`    | `CLOSED`, `IN_PROGRESS`       |
| `CLOSED`      | *(terminal — no transitions)* |

Invalid transitions return `422 Unprocessable Entity` with an explanation.

---

## Case History

Every status change writes an immutable `case_history` record:

| Field        | Description |
|--------------|-------------|
| `old_status` | Previous status (null on initial creation) |
| `new_status` | Status after the transition |
| `comment`    | Optional annotation supplied in the PATCH body |
| `changed_by` | Currently `"system"` — placeholder until auth (Week 4) |
| `created_at` | UTC timestamp |

The case update and history record are committed in **one atomic transaction**.

> **Limitation:** `changed_by` is a placeholder. Real user identity requires
> authentication, which is planned for Week 4.

---

## Request Correlation

Every response carries an `X-Request-ID` header. Pass your own
`X-Request-ID` request header and it will be echoed back, allowing you to
correlate client requests with server logs.

---

## Logging

Format: `YYYY-MM-DDTHH:MM:SS | LEVEL | module | message`

Key events logged:
- Application startup
- Case creation (`case_created`)
- Status transitions (`case_status_transition old_status= new_status=`)
- Case updates
- Important failures (not found, invalid transition)

**Not logged:** passwords, database credentials, API keys.

---

## Current Limitations

- No authentication or authorization (Week 4)
- `changed_by` in case history is a development placeholder
- No AI, RAG, or LLM integrations (Weeks 3–5)
- No data ingestion or generation pipelines (Week 2)
- No frontend
- No async endpoints (synchronous SQLAlchemy for Week 1)

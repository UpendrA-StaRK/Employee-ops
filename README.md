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

## API Endpoints

### Employees
- `POST /employees` — Create a new employee
- `GET /employees/{employee_id}` — Retrieve an employee by ID

### Cases
- `POST /cases` — Create a case for an employee (always starts `OPEN`)
- `GET /cases` — List and filter cases (`employee_id`, `status`, `category`, `priority`)
- `GET /cases/{case_id}` — Retrieve a case by ID
- `PATCH /cases/{case_id}` — Update a case; validates status lifecycle rules
- `GET /cases/{case_id}/history` — Retrieve status history in chronological order

---

## Case Lifecycle

Every case starts as `OPEN`. Status transitions are strictly validated:

```
OPEN ──────────────────────────────────────────── CLOSED
  │                                                  ▲
  └──► IN_PROGRESS ──► PENDING ──► RESOLVED ────────┘
             ▲             │            │
             └─────────────┘            └──► IN_PROGRESS (reopened)
```

**Allowed transitions:**

| From          | To                          |
|---------------|-----------------------------|
| `OPEN`        | `IN_PROGRESS`, `CLOSED`     |
| `IN_PROGRESS` | `PENDING`, `RESOLVED`       |
| `PENDING`     | `IN_PROGRESS`, `RESOLVED`   |
| `RESOLVED`    | `CLOSED`, `IN_PROGRESS`     |
| `CLOSED`      | *(terminal — no transitions)* |

Invalid transitions (e.g. `OPEN → RESOLVED`) return **422 Unprocessable Entity**.

**Supported Categories:** `LEAVE`, `PAYROLL`, `BENEFITS`, `ACCESS`, `GENERAL`

**Supported Priorities:** `LOW`, `MEDIUM`, `HIGH`, `URGENT`

---

## Case History

Every status transition creates an immutable `case_history` record containing:
- `old_status` — previous status (null for initial creation)
- `new_status` — status after the transition
- `comment` — optional annotation supplied with the PATCH request
- `changed_by` — currently `"system"` (placeholder; real user identity requires authentication)
- `created_at` — timestamp of the change

The case update and its history record are committed **atomically** — if either fails, neither is persisted.

> **Limitation:** `changed_by` is a development placeholder (`"system"`). Real user identity will be populated when authentication is introduced (Week 4).

---

## Current Limitations

- No authentication or authorization.
- No AI, RAG, or LLM integrations.
- No data ingestion or generation pipelines.
- No frontend.
- `changed_by` in case history is a placeholder; real identity comes with auth (Week 4).


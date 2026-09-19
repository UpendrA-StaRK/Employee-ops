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

## Synthetic Data Generator

A deterministic, reproducible synthetic data generator is provided for development and testing. It generates realistic `Employee`, `Case`, and `CaseHistory` records using only the Python standard library.

### Generation (CLI)

The generator runs independently of the production app and exports CSV and JSON to `data/generated/`.

```bash
# Generate 100 employees and 200 cases using the default clean scenario
uv run python -m generators.generate --seed 42

# Configure volume
uv run python -m generators.generate --employees 500 --cases 2000 --scenario clean --seed 42
```

### Database Seeding

The seeder inserts the generated data into your local development database. It is **non-destructive** by default (existing records are skipped).

```bash
uv run python -m generators.seed

# DESTRUCTIVE: truncate existing data before seeding
uv run python -m generators.seed --clean
```

### Data Scenarios

The generator supports testing different data quality scenarios (used in Week 2):

- `clean`: Valid consistent data, matching all relations and constraints.
- `duplicates`: Introduces duplicate employee/case records.
- `missing_fields`: Introduces missing mandatory fields (e.g., null subject/email).
- `invalid_values`: Introduces invalid enums, malformed emails, and invalid dates.
- `orphan_records`: Introduces broken foreign keys (cases referencing missing employees).

```bash
uv run python -m generators.generate --scenario duplicates --seed 42
```

---

## Data Model

The core domain model focuses on Employee Operations. The synthetic generator is purely for test data and contains no real employee information.

```
Employee (1) ──────── (many) Case
                               │
                               │ (1)
                               │
                             (many)
                          CaseHistory
```

- **Employee**: Represents a worker with contact details and department.
- **Case**: A specific request or issue raised for an employee (e.g., payroll, leave, access).
- **CaseHistory**: An immutable log of status transitions for a specific case.

---

## Architecture

### FDE Solution Anatomy (5-Tier Architecture)

The KPMG FDE curriculum spans five architectural layers, which will be built progressively over 5 weeks:
1. **UI Layer** — (Not in scope yet)
2. **API Layer** — FastAPI REST endpoints, Pydantic schemas, routing. (Built Week 1)
3. **Data Layer** — PostgreSQL, SQLAlchemy ORM, Alembic migrations, Data Pipelines. (Built Week 1 & 2)
4. **AI Layer** — RAG, Vector Index, LLM generation, Multi-Tool workflows. (Weeks 3 & 4)
5. **Integration Layer** — Human-in-the-loop approvals, external tool calls. (Week 4)

### API Request Flow

```text
Client
  ↓
FastAPI Router (app/api/)      ← Thin layer: routing, schema validation, HTTP codes
  ↓
Service (app/services/)        ← Domain logic, lifecycle rules, transaction commit
  ↓
Repository (app/repositories/) ← Database access, SQLAlchemy ORM flush
  ↓
PostgreSQL
```

**Pattern:** Repositories only `flush()`. Services own `db.commit()`. This means multi-step operations (like updating a case and inserting a history record) are committed atomically in a single transaction.

### Data Generation Flow

```text
Generator (generators/)        ← Deterministic, stdlib-only
  ↓
Synthetic Data                 ← CSV / JSON exports
  ↓
Development/Test Database      ← Seeder utility
```

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

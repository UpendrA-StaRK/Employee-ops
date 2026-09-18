## Project Overview

This project is an **AI-powered Employee Management / Employee Operations System** designed to manage employee-related operational cases, documents, policies, and workflows in one system. It will combine a frontend, backend APIs, database, AI capabilities, document/data processing, and integrations to demonstrate an end-to-end FDE solution.

### Project Preview

The system will allow employees and HR/operations teams to raise, manage, track, and resolve employee-operation cases such as **leave, onboarding, employee documents, policy-related queries, and other HR requests**.

The system will maintain **active and historical cases**, employee information, relevant documents and policies, and case activity/history. AI capabilities will help with tasks such as **understanding employee requests, retrieving relevant policy information, generating responses or summaries, and assisting with case resolution**.

The project will start with a **small end-to-end MVP** and progressively expand week-by-week as new FDE concepts from the curriculum are learned and implemented.

The project will also include a **data/document generation capability** to generate realistic synthetic employee records, cases, policy documents, and supporting datasets required to develop and test the system throughout the curriculum.

## Project Objective

The primary objective of this project is to build the system while simultaneously using it as a learning vehicle for the FDE curriculum.

The project should:

* Start with a clearly defined **MVP**.
* Cover the curriculum progressively **week by week**.
* Distinguish between:

  * **What must be learned before coding**
  * **What can be learned while implementing**
  * **What should be learned after implementation / during expansion**
* Use the project itself to reinforce the concepts in the curriculum.
* Prefer practical implementation over isolated theoretical learning.
* Expand from the MVP into additional capabilities only after the MVP is functional.

## Source of Truth

### Curriculum

See:

"C:\Users\USER\Desktop\Learning Kpmg\Fresher AI Training_Curriculam_Sep2026.md"

The curriculum file is the authoritative source for:

* Weekly learning requirements
* Required concepts
* Technology stack
* Tools/frameworks
* Expected capabilities
* Any prescribed project/implementation requirements

**Important:** Read the curriculum file at the start of every session before making decisions that could affect:

* Technology stack
* Architecture
* Weekly scope
* Learning sequence
* Project implementation
* Dependencies
* Development tools

Do not duplicate the curriculum inside this memory file. Reference it instead.

If the curriculum and an earlier project decision conflict:

1. Identify the conflict.
2. Do not silently change the stack or scope.
3. Explain the conflict.
4. Record the decision/reversal in the Decisions Log.

### Other Project Sources

Additional authoritative project sources may include:

* Project requirements
* Design documents
* Architecture documents
* Presentations
* Existing code
* Dataset specifications
* API specifications
* User-approved decisions

When sources conflict, prefer the **most recent explicitly approved decision**, unless the curriculum requires otherwise.

---

# Standing Rules

These rules apply to every agent/model working on this repository.

## 1. Start-of-Session Protocol

At the start of every session:

1. Read this memory file in full.
2. Read `<CURRICULUM_FILE_PATH>` in full or retrieve the relevant complete sections.
3. Inspect the current repository/project state when implementation work is requested.
4. Review the **Current State / Open Threads**.
5. Review recent **Decisions Log** and **Session History** entries.
6. Do not ask the user to re-explain context already recorded here.
7. Before making a stack-affecting decision, verify it against the curriculum.

If required information is genuinely unavailable, ask only for the missing information.

Commit Rule: Do not commit changes automatically. Wait until I explicitly say “commit”. If I say “changes”, make the requested changes first and commit only after I subsequently say “commit”.

---

## 2. Learning-First Rule

Before writing substantial code, identify the concepts that need to be understood first.

For each major implementation task, classify knowledge into:

### Must Learn Before Coding

Concepts where misunderstanding would likely lead to incorrect architecture or implementation.

### Learn While Coding

Concepts that are best understood through implementation and experimentation.

### Learn After / Expansion

Concepts that are useful but not required for the current MVP.

Do not unnecessarily delay implementation by requiring mastery of every related concept beforehand.

After Each Part / Week: At the end of every learning or implementation part, explicitly state what has been learned, what remains to be learned, what should be learned before the next part, and the required level of understanding for each topic (e.g., awareness, basic understanding, working knowledge, implementation-level proficiency, or production-level understanding). Do not proceed to the next part if a prerequisite concept has not been learned to the required level.

---

## 3. Curriculum-to-Project Mapping

Every significant weekly curriculum requirement should eventually map to one or more of:

* Project feature
* Architecture component
* API
* Database model
* AI capability
* Integration
* Test
* Dataset
* Documentation
* Developer workflow

When useful, explicitly state:

`Curriculum concept → Project implementation → Evidence of learning`

Do not add artificial features merely to claim curriculum coverage.

---

## 4. MVP-First Rule

The project should be developed in stages:

### MVP

The smallest complete system that demonstrates the core end-to-end workflow.

### Curriculum Coverage

Additional capabilities required to exercise the relevant weekly learning objectives.

### Expansion

Useful production-like capabilities that are not necessary for the MVP.

For every proposed feature, identify whether it is:

* `MVP`
* `Curriculum-required`
* `Post-MVP`
* `Optional`

Avoid scope creep.

---

## 5. Architecture Decision Rule

For non-trivial architectural decisions, consider:

* Simplicity
* Curriculum alignment
* Learning value
* Maintainability
* Extensibility
* Security
* Testing
* Cost
* Development speed
* Production realism

Do not introduce a technology solely because it is popular if it conflicts with the curriculum or adds unnecessary complexity.

---

## 6. Technology Stack Rule

The curriculum is the primary source of truth for the technology stack.

Do not replace or add major technologies without documenting:

* What is changing
* Why it is needed
* Whether it is required by the curriculum
* What alternatives were considered
* What parts of the project are affected

Small implementation libraries do not necessarily require a formal decision if they do not materially affect architecture.

---

## 7. Data Rule

The project must have realistic data sufficient to test the system.

When a feature requires data, define:

* Data sources
* Data schema
* Required fields
* Relationships
* Expected volume
* Data generation method
* Synthetic vs real data
* Edge cases
* Invalid/missing data
* Privacy considerations
* How the data will be loaded into the system

For synthetic project data, prefer reproducible generation so datasets can be regenerated consistently.

Data required for future weeks should be planned early where practical, without unnecessarily implementing future features.

---

## 8. AI / Generator Rule

If the project includes an AI/data/document generator, treat generation as a first-class project capability.

Clearly distinguish:

* Source/reference data
* Generated raw data
* Generated documents
* Generated structured records
* AI-generated content
* Human-provided content
* Test fixtures

Generated data should be realistic enough to exercise:

* Normal cases
* Edge cases
* Failure cases
* Ambiguous cases
* Missing information
* Conflicting information
* Large inputs where relevant

Generation should be reproducible where practical.

---

## 9. Implementation Rule

Before implementing a significant feature:

1. Explain the goal.
2. Identify prerequisites.
3. Identify relevant curriculum concepts.
4. Identify the architecture impact.
5. Define the smallest implementation.
6. Implement.
7. Test.
8. Explain what was learned.
9. Record any non-trivial architectural decision.

Do not write large amounts of code before establishing the intended design.

---

## 10. Testing Rule

Every meaningful feature should have an appropriate testing strategy.

Consider:

* Unit tests
* API tests
* Integration tests
* Database tests
* AI evaluation
* Data validation
* Authentication/authorization tests
* Error handling
* Edge cases
* End-to-end workflows

For AI features, do not rely only on whether the application "runs." Define what constitutes a useful/acceptable output.

---

## 11. Security Rule

Security should be considered from the beginning rather than added only at the end.

Pay particular attention to:

* Authentication
* Authorization
* Secrets
* Environment variables
* Input validation
* API security
* File uploads
* Prompt injection where applicable
* Sensitive data
* Logging
* Access control
* AI-generated actions

Never commit credentials, API keys, tokens, or other secrets.

---

## 12. Documentation Rule

Important project decisions and architecture should be documented sufficiently for another developer/agent to continue the work.

Do not create excessive documentation for trivial changes.

Documentation should prioritize:

* Architecture
* Setup
* Important workflows
* APIs
* Data models
* AI behavior
* Decisions
* Known limitations

---

# Decision Logging

## Decisions Log

<!-- Append-only. Never delete or rewrite historical decisions. -->

Format:

* YYYY-MM-DD: **<decision>** — <why this decision was made> — <what it affects>

For non-trivial decisions, include enough context that a future agent can understand why the decision exists.

Examples of decisions that should normally be logged:

* Architecture choices
* Technology choices
* Database choices
* API design choices
* AI approach
* Data-generation approach
* Authentication approach
* MVP scope decisions
* Major dependency choices
* Important trade-offs
* Rejected alternatives

### Reversing a Decision

Never edit an old decision.

If a previous decision is changed, append a new entry:

* YYYY-MM-DD: **Reversed <previous decision>** — <why the previous decision is no longer appropriate> — <new decision and affected components>

### Week 1 Decisions

* 2026-09-18: **Use `uv` for dependency/environment management** — Prescribed by task requirements; modern, fast, and replaces pip/venv/pip-tools in one tool — affects all dependency installation and environment setup.
* 2026-09-18: **Use `pyproject.toml` as the single source of truth for dependencies** — Prescribed by task; no requirements.txt created — affects how deps are declared and installed.
* 2026-09-18: **Use `hatchling` as the build backend** — Default for `uv init`; lightweight and PEP 517 compliant; no reason to change — affects editable installs and wheel builds.
* 2026-09-18: **Separate dev dependencies using `[project.optional-dependencies] dev`** — Keeps runtime image slim; install with `uv sync --extra dev` — affects CI and production deployment.
* 2026-09-18: **Use synchronous SQLAlchemy engine (psycopg2) for Week 1** — Simplest foundation; no async endpoints exist yet; asyncpg installed as dependency for future use — affects db/session.py engine setup.
* 2026-09-18: **Health endpoint reports DB unavailability in body, not via HTTP status code** — Process-level orchestration (Docker, k8s) should distinguish "service down" from "service degraded"; always returning 200 is intentional — affects GET /health response contract.
* 2026-09-18: **Alembic initialized with `alembic/` directory; sqlalchemy.url overridden from app settings in env.py** — Single source of truth for DATABASE_URL; avoids duplication between alembic.ini and .env — affects migration workflow.
* 2026-09-18: **No `__init__.py` in `generators/`, `data/`, `sql/`, `docs/`** — These directories are not Python packages; they hold scripts/data/assets — correct per Python packaging conventions.
* 2026-09-18: **Use `psycopg[binary]` instead of `psycopg2-binary`** — Modern psycopg3 natively supports standard Python datetime/timezone management seamlessly and handles the `postgresql+psycopg://` URI.
* 2026-09-18: **Use `StaticPool` and transactions for testing** — Ensures isolated tests without accidentally mutating or wiping the local development database by connecting to a separate `employee_ops_test` DB and rolling back after each test fixture.
* 2026-09-18: **Remove hardcoded database credentials** — Made `database_url` in config strictly depend on `.env` (no default with fake credentials) and dynamically derive the test URL.
* 2026-09-18: **Employee Deletion Strategy** — Do not hard delete employees. Use soft deletes (e.g., `status = 'INACTIVE'`) or a historical audit table to maintain historical case integrity for left/deleted employees. To be fully implemented in a future phase.

---

# Session History

## Session History

<!-- Append-only. Never delete or rewrite historical entries. -->

Format:

* YYYY-MM-DD HH:MM (timezone) | Model: <model name> | Device: <device/hostname> — <what was completed> — <what remains / next step>

At the end of **every session**, append an entry, including sessions that were:

* Exploratory
* Planning-only
* Short
* Debugging-focused
* Documentation-focused

Use the real date/time and model name.

Determine the device/hostname from the execution environment when possible.

If the exact time or device/hostname cannot be determined reliably, **ask the user rather than guessing**.

* 2026-09-18 15:24 (IST) | Model: Claude Sonnet 4.6 (Thinking) | Device: UPENDRA — Week 1 Task 01 complete: uv project initialized, pyproject.toml, FastAPI app, GET /health, pydantic-settings config, logging, SQLAlchemy session foundation, Alembic init, 6 passing pytest tests, .gitignore, .env.example, README.md, initial git commit (32 files) — Next: Week 1 Task 02 (employee/case CRUD, DB models) or Week 2 data ingestion depending on curriculum schedule.
* 2026-09-18 16:30 (IST) | Model: Gemini 3.1 Pro (High) | Device: UPENDRA — Week 1 Task 02 (Database + Employee Domain) complete: Employee model, Alembic migration, schemas, repository, service, FastAPI endpoints, and tests implemented. Hardcoded database credentials removed. — Next: Case CRUD, DB models or Week 2 data ingestion depending on curriculum schedule.
* 2026-09-18 17:15 (IST) | Model: Gemini 3.1 Pro (High) | Device: UPENDRA — Week 1 Task 03 (Case Management Domain) complete: Case model with Enums, Alembic migration, schemas, repository, service, and FastAPI endpoints implemented. Added testing and updated README. — Next: Week 2 Data ingestion.

---

# Current State / Open Threads

<!-- This section is NOT append-only. Overwrite it at the end of every session. -->

## Current Phase

* Week 1 — Project Foundation, Employee & Case Domain (Part 3 complete)

## Completed

* Week 1 Part 3: Case Management vertical slice
  * `app/models/case.py` — SQLAlchemy model with Enums
  * Alembic migration generated and applied
  * `app/schemas/case.py` — Pydantic schemas 
  * `app/repositories/case.py` — Repository layer
  * `app/services/case.py` — Service layer with employee validation logic
  * `app/api/case.py` — FastAPI endpoints with query parameter filtering
  * `tests/api/test_case.py` — API tests for Case domain (all passing)
* Week 1 Task 02: Database + Employee Domain vertical slice
  * `app/models/employee.py` — SQLAlchemy model
  * Alembic migration generated and applied
  * `app/schemas/employee.py` — Pydantic schemas (Create, Response)
  * `app/repositories/employee.py` — Repository layer
  * `app/services/employee.py` — Service layer with business logic
  * `app/api/employee.py` — FastAPI endpoints (POST /employees, GET /employees/{id})
  * `tests/conftest.py` — Test DB setup with `StaticPool` and transactions
  * `tests/api/test_employee.py` — API tests (all passing)
* Week 1 Task 01: Full project foundation implemented and committed to git
  * uv project initialized (`employee-ops-ai`)
  * `pyproject.toml` with runtime and dev dependencies
  * `app/main.py` — FastAPI application
  * `app/api/health.py` — GET /health endpoint
  * `app/core/config.py` — pydantic-settings configuration
  * `app/core/logging.py` — minimal logging setup
  * `app/db/session.py` — SQLAlchemy engine/session/Base foundation
  * `alembic/` — migrations initialized, wired to app settings
  * `tests/api/test_health.py` — 6 tests, all passing
  * `.env.example`, `.gitignore`, `README.md`
  * Git repository initialized, initial commit made

## In Progress

* None

## Next

* Proceed to Week 2 (Data ingestion, quality, pipelines) based on curriculum schedule.

## Week 1 Learning Summary

* **What has been learned:** Implementation-level proficiency in setting up a FastAPI project, SQLAlchemy (with `psycopg3`), Alembic migrations, database testing with transaction rollbacks, Pydantic data validation, and creating dependent relational entities (Cases) with Enums.
* **What remains to be learned:** Implementing Case History (audit trailing), AI workflows (RAG), and data ingestion.
* **Should be learned before next part (Week 2):** Basic understanding of data pipelines, synthetic data generation approaches, and data validation techniques.

## Blocked / Needs Decision

* None — Week 1 Task 01 is fully complete

## Known Technical Debt

* Two deprecation warnings from httpx/starlette TestClient — not errors; library ecosystem version compatibility issue; monitor for resolution in a future release.
* `asyncio_default_fixture_loop_scope` warning from pytest-asyncio — configure in pyproject.toml in Week 2 when async tests are written.

## Open Questions

* None for Week 1 Task 01

## Current MVP Boundary

### Inside MVP (Week 1)
* FastAPI application with GET /health
* Environment-based configuration
* Logging foundation
* SQLAlchemy session foundation
* Alembic migrations
* pytest infrastructure
* **Employee CRUD (Database + Employee Domain)**
* **Case CRUD (Database + Case Domain)**

### Explicitly Outside MVP (not yet)
* Database models (CaseHistory, Audit tables, etc.)
* Authentication/authorization
* AI, RAG, LLM integrations
* Data ingestion pipelines
* Frontend
* Synthetic data generation

## Curriculum Progress

* Week 1: `Implemented` (Task 01 complete; additional tasks may follow)
* Week 2: `Not started`
* Week 3: `Not started`
* Week 4: `Not started`
* Week 5: `Not started`

---

# Agent Working Principles

When working on this project:

* Preserve existing decisions unless there is a concrete reason to change them.
* Do not silently change architecture.
* Do not silently introduce major dependencies.
* Do not duplicate information that already exists in authoritative project files.
* Do not ask the user questions whose answers already exist in project memory, curriculum files, or project artifacts.
* Ask questions when a decision materially affects architecture, scope, cost, security, or learning objectives and the available context is insufficient.
* Prefer the smallest working implementation before adding abstractions.
* Prefer explicit trade-offs over arbitrary choices.
* Keep the implementation aligned with the learning objective.
* Do not optimize prematurely.
* Do not build future-week functionality unless it is intentionally part of the current plan.
* When something is uncertain, label it as an assumption rather than presenting it as a fact.
* When a requirement is ambiguous, clarify before making an irreversible decision.

---

# Session Completion Checklist

Before ending a session:

* [ ] Current State / Open Threads has been updated.
* [ ] All non-trivial decisions made during the session have been added to Decisions Log.
* [ ] Session History has been appended.
* [ ] Curriculum alignment has been checked for relevant work.
* [ ] Tests/status are recorded where applicable.
* [ ] Known blockers and next steps are recorded.
* [ ] No previous history or decisions were deleted or rewritten.

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

User-Controlled Execution Rule: Do not automatically run tests, builds, migrations, installs, expensive commands, or other token/time-consuming verification steps. Before running such commands, clearly tell me what will be run and why, and wait for my explicit approval. Similarly, do not commit changes automatically; always wait for my explicit “commit” instruction before committing.

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

Learning Must Be Explicit: A concept must not be considered “learned” merely because it was used or implemented in code. Before marking a curriculum topic as learned, explicitly teach/explain the concept to the required depth, confirm understanding through questions or a small exercise where appropriate, and then apply it in the project. Code implementation is evidence of application, not evidence of learning by itself.

After Each Part / Week: Explicitly report (1) concepts that were actually taught and learned, (2) concepts only applied through code but not yet learned, (3) concepts still to be learned, (4) what must be learned before the next part, and (5) the required learning level for each concept — awareness, basic understanding, working knowledge, implementation-level proficiency, or production-level understanding. Do not mark a topic as learned solely because it appeared in the code. Do not proceed past a prerequisite topic until it has been learned to the required level.

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
* 2026-09-18: **Repositories flush; services commit** — All repositories use `db.flush()` only. The service layer owns `db.commit()` so that multi-step operations (e.g., case update + history record) execute as one atomic transaction.
* 2026-09-18: **Explicit status transition table** — Lifecycle rules are a plain Python dict (`ALLOWED_TRANSITIONS`) in the service layer. No state-machine library, no workflow engine. Easy to read and extend.
* 2026-09-18: **Initial case history record on creation** — When a case is created, one history record is written with `old_status=None`, `new_status=OPEN`. Provides a complete audit trail from day one.
* 2026-09-18: **`changed_by` placeholder** — Defaults to `"system"`. Real user identity requires authentication (Week 4). Documented in API docstrings and README.
* 2026-09-18: **Migration Enum reuse** — `case_history` table reuses the PostgreSQL `case_status_enum` type already created by the `cases` migration. Fixed by using `postgresql.ENUM(..., create_type=False)` in the Alembic migration.
* 2026-09-18: **Engineering hardening & cleanup** — Removed unused `psycopg2-binary`, `asyncpg`, `python-dotenv` dependencies; unified dev dependencies; added Request-ID correlation middleware; added unit test suites (`test_case_transitions.py`, `test_session.py`); achieved 100% test coverage across `app/` (74/74 tests passing).
* 2026-09-18: **Synthetic Data Generator (Zero-Dependency)** — Designed `generators` module strictly using Python stdlib (no `Faker` or external libs) to guarantee 100% determinism via `random.Random(seed)`, keeping dev environment light and reproducible. Generator is completely decoupled from the production API.
* 2026-09-18: **Deterministic Lifecycle History Generation** — Reused `ALLOWED_TRANSITIONS` rules in the generator to simulate 0–4 valid status transitions per case, guaranteeing that generated case histories are chronological and terminal statuses match exactly.
* 2026-09-18: **Non-Destructive Database Seeder** — `generators.seed` inserts missing records by checking existing IDs first, rather than blindly truncating or deleting. Ensures developer data isn't unexpectedly wiped unless `--clean` is explicitly passed.

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

* 2026-09-18 15:24 (IST) | Model: Claude Sonnet 4.6 (Thinking) | Device: UPENDRA — Week 1 Part 1 complete: uv project, FastAPI, GET /health, config, logging, SQLAlchemy, Alembic, pytest, git.
* 2026-09-18 16:30 (IST) | Model: Gemini 3.1 Pro (High) | Device: UPENDRA — Week 1 Part 2 complete: Employee model, migration, schemas, repo, service, endpoints, tests.
* 2026-09-18 17:15 (IST) | Model: Gemini 3.1 Pro (High) | Device: UPENDRA — Week 1 Part 3 complete: Case model, migration, schemas, repo, service, endpoints, tests.
* 2026-09-18 20:20 (IST) | Model: Claude Sonnet 4.6 (Thinking) | Device: UPENDRA — Week 1 Part 4 complete: CaseHistory model, lifecycle transition rules, atomic case+history commit, GET /cases/{id}/history, 24 new tests, 44/44 passing.
* 2026-09-18 20:30 (IST) | Model: Claude Sonnet 4.6 (Thinking) / Gemini 3.8 Flash | Device: UPENDRA — Week 1 Part 5 complete: Engineering hardening, removed unused deps, fixed warnings, added unit test suites, 74/74 tests passing, 100% test coverage.
* 2026-09-18 20:47 (IST) | Model: Gemini 3.1 Pro (High) | Device: UPENDRA — Week 1 Part 6 complete: Synthetic Data Generator (core, CLI, db seeder, tests, docs), Final Week 1 review. — Next: Week 2 (Enterprise Data Pipeline).

---

# Current State / Open Threads

<!-- This section is NOT append-only. Overwrite it at the end of every session. -->

## Current Phase

* Week 1 — All 6 Parts complete. Final Review completed. Ready for Week 2.

## Completed

* Week 1 Part 6: Synthetic Data Generator + Final Week 1 Review
  * `generators/generator.py`: Core zero-dependency deterministic generator
  * `generators/generate.py`: CLI supporting scenario mutations and CSV/JSON output
  * `generators/seed.py`: Non-destructive database seeder tool
  * `tests/unit/test_generator.py`: Test suite validating generator output, FK integrity, and transitions
  * Documentation updated with generator flow and comprehensive Week 1 review
* Week 1 Part 5: Engineering Hardening
  * Dependency cleanup: removed unused `psycopg2-binary`, `asyncpg`, `python-dotenv` from `pyproject.toml` and `uv.lock`
  * Dev dependencies unified into `[project.optional-dependencies] dev`
  * Configured pytest coverage with 100% branch and statement coverage (74/74 tests passing)
  * Configured `asyncio_default_fixture_loop_scope` to eliminate pytest-asyncio warning
  * Added lightweight Request-ID middleware in `app/main.py` returning `X-Request-ID` header
  * Added unit test suites (`tests/unit/test_case_transitions.py`, `tests/unit/test_session.py`)
  * Added missing branch/error path tests in `tests/api/test_case.py`
  * Hardened `README.md`, `.env.example`, and `.gitignore`
* Week 1 Part 4: Case History + Lifecycle Rules
  * `app/models/case_history.py` — CaseHistory SQLAlchemy model
  * Alembic migration with Enum reuse fix (`create_type=False`)
  * `app/schemas/case_history.py` — CaseHistoryResponse schema
  * `app/repositories/case_history.py` — flush-only repository
  * `app/services/case.py` — rewritten: `ALLOWED_TRANSITIONS` dict, atomic commit
  * `app/api/case.py` — rewritten: `GET /cases/{id}/history`, 422 on invalid transition
  * `tests/api/test_case_history.py` — 24 tests (all passing)
  * All repos unified to flush-only; services own commit
* Week 1 Part 3: Case Management vertical slice
* Week 1 Part 2: Database + Employee Domain vertical slice
* Week 1 Part 1: Project foundation
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

* Proceed to **Week 2** (Data ingestion, quality, pipelines).

## Week 1 Learning Summary

### Concepts Applied in Code (not yet formally taught)
* SQLAlchemy 2.x `Mapped` / `mapped_column` ORM style
* Alembic autogenerate and manual migration fixups
* Pydantic v2 `model_copy`, `model_dump(exclude_unset=True)`
* psycopg3 driver differences vs psycopg2
* PostgreSQL named Enum type reuse across tables

### Must Learn Before Week 2
* **Data pipelines** — awareness of batch vs stream, ETL vs ELT
* **Data quality** — basic understanding of validation, nulls, duplicates
* **Synthetic data generation** — working knowledge of Faker / structured generators
* **CSV/JSON ingestion** — implementation-level (reading, validating, loading)

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
* **Case History + Lifecycle Rules**

### Explicitly Outside MVP (not yet)
* Database models (Audit tables for employees, etc.)
* Authentication/authorization (Week 4)
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

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

---

# Current State / Open Threads

<!-- This section is NOT append-only. Overwrite it at the end of every session. -->

## Current Phase

* <e.g. Planning / MVP development / Week 2 implementation>

## Completed

* <completed item>
* <completed item>

## In Progress

* <current item>
* <current item>

## Next

* <next item>
* <next item>

## Blocked / Needs Decision

* <blocker or "None">

## Known Technical Debt

* <technical debt or "None">

## Open Questions

* <question or "None">

## Current MVP Boundary

* <what is currently inside the MVP>
* <what is explicitly outside the MVP>

## Curriculum Progress

* Week <N>: <status>
* Week <N>: <status>

Use statuses such as:

* `Not started`
* `Learning`
* `Implementing`
* `Implemented`
* `Tested`
* `Complete`

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

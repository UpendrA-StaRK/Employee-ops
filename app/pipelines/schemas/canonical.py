"""Canonical schema definitions for the Employee Operations pipeline.

A **schema** describes the expected structure and types of a standardized entity
record — field names, Python types, required/optional status, nullability, and
which fields identify the entity.

Schemas are NOT responsible for:
  - Business-rule validation (e.g. "is this status value allowed?") — Part 6
  - Referential integrity (e.g. "does this employee_id exist?") — Part 6
  - Transformation or cleaning — that belongs to standardize.py

Each schema class carries two class-level constants:

    SCHEMA_VERSION : str
        Identifies this schema revision in the format ``"<entity>.<version>"``.
        Example: ``"employee.v1"``

    IDENTIFIER_FIELDS : tuple[str, ...]
        The field name(s) that uniquely identify a record of this entity.
        Example: ``("employee_id",)``

Field nullability decisions
---------------------------
Fields that the standardization layer may legally set to None are declared
``Optional[<type>]`` (i.e. nullable).  Whether a None value is *acceptable*
for the business is a Data Quality concern (Part 6), not a schema concern.

  employee_id, name, email — required + non-nullable (domain: NOT NULL in DB,
      structural identifier; a record without these cannot be routed)

  department, job_title, status — required + nullable (standardizer strips
      empty strings → None; DQ will decide whether None is acceptable)

  created_at, updated_at — required + nullable (standardizer returns None for
      unparseable dates; DQ will decide whether None is acceptable)

  old_status (CaseHistory) — required + nullable by design (None for the
      initial history record of a new case)

  comment (CaseHistory) — optional + nullable (may be absent from source)

  changed_by (CaseHistory) — required + nullable

Schema versions
---------------
Version identifiers follow ``<entity>.<version>`` convention and are
intentionally simple — no registry, no external service.

    employee.v1
    case.v1
    case_history.v1
    department_reference.v1

Evolution rules (see also contracts.py):
    Compatible (non-breaking):
        - Adding a new optional/nullable field
    Potentially breaking:
        - Removing any existing field
        - Changing a field type incompatibly
        - Renaming an identifier field
        - Making a nullable field non-nullable
"""
from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Employee schema
# ---------------------------------------------------------------------------

class EmployeeSchemaV1(BaseModel):
    """Canonical schema for a standardized employee record.

    Schema version: employee.v1
    Identifier:     employee_id
    """

    model_config = ConfigDict(strict=False)

    # ClassVar constants — not Pydantic fields
    SCHEMA_VERSION: ClassVar[str] = "employee.v1"
    IDENTIFIER_FIELDS: ClassVar[tuple[str, ...]] = ("employee_id",)

    # ── Required, non-nullable ─────────────────────────────────────────────
    employee_id: str
    """Unique identifier for the employee.  Required.  Non-nullable."""

    name: str
    """Full name of the employee.  Required.  Non-nullable."""

    email: str
    """Email address.  Required.  Non-nullable."""

    # ── Required, nullable ─────────────────────────────────────────────────
    department: Optional[str] = None
    """Department name.  Required field.  Nullable — standardizer may produce
    None when the source value is empty."""

    job_title: Optional[str] = None
    """Job title.  Required field.  Nullable — same reasoning as department."""

    status: Optional[str] = None
    """Employment status string (e.g. 'ACTIVE', 'INACTIVE').  Nullable."""

    created_at: Optional[datetime] = None
    """UTC timestamp of record creation.  Nullable — standardizer sets None
    when the source date cannot be parsed (structural failure, not DQ)."""

    updated_at: Optional[datetime] = None
    """UTC timestamp of last update.  Nullable — same reasoning as created_at."""


# ---------------------------------------------------------------------------
# Case schema
# ---------------------------------------------------------------------------

class CaseSchemaV1(BaseModel):
    """Canonical schema for a standardized case record.

    Schema version: case.v1
    Identifier:     case_id
    """

    model_config = ConfigDict(strict=False)

    SCHEMA_VERSION: ClassVar[str] = "case.v1"
    IDENTIFIER_FIELDS: ClassVar[tuple[str, ...]] = ("case_id",)

    # ── Required, non-nullable ─────────────────────────────────────────────
    case_id: str
    """Unique identifier for the case.  Required.  Non-nullable."""

    employee_id: str
    """Foreign key to the owning employee.  Required.  Non-nullable."""

    # ── Required, nullable ─────────────────────────────────────────────────
    category: Optional[str] = None
    """Case category string (e.g. 'LEAVE', 'PAYROLL').  Nullable."""

    subject: Optional[str] = None
    """Short case subject.  Nullable."""

    description: Optional[str] = None
    """Full case description.  Nullable."""

    status: Optional[str] = None
    """Case lifecycle status string (e.g. 'OPEN', 'CLOSED').  Nullable."""

    priority: Optional[str] = None
    """Priority string (e.g. 'LOW', 'HIGH').  Nullable."""

    created_at: Optional[datetime] = None
    """UTC timestamp of case creation.  Nullable."""

    updated_at: Optional[datetime] = None
    """UTC timestamp of last update.  Nullable."""


# ---------------------------------------------------------------------------
# CaseHistory schema
# ---------------------------------------------------------------------------

class CaseHistorySchemaV1(BaseModel):
    """Canonical schema for a standardized case history record.

    Schema version: case_history.v1
    Identifier:     history_id
    """

    model_config = ConfigDict(strict=False)

    SCHEMA_VERSION: ClassVar[str] = "case_history.v1"
    IDENTIFIER_FIELDS: ClassVar[tuple[str, ...]] = ("history_id",)

    # ── Required, non-nullable ─────────────────────────────────────────────
    history_id: str
    """Unique identifier for this history record.  Required.  Non-nullable."""

    case_id: str
    """Foreign key to the parent case.  Required.  Non-nullable."""

    new_status: str
    """The status the case transitioned TO.  Required.  Non-nullable."""

    # ── Required, nullable ─────────────────────────────────────────────────
    old_status: Optional[str] = None
    """The status the case transitioned FROM.  Nullable — None for the initial
    history record when a case is first created."""

    changed_by: Optional[str] = None
    """Actor who made the change.  Nullable."""

    created_at: Optional[datetime] = None
    """UTC timestamp of this history event.  Nullable."""

    # ── Optional, nullable ─────────────────────────────────────────────────
    comment: Optional[str] = None
    """Free-text annotation.  Optional — may be absent from the source record."""


# ---------------------------------------------------------------------------
# DepartmentReference schema
# ---------------------------------------------------------------------------

class DepartmentReferenceSchemaV1(BaseModel):
    """Canonical schema for a standardized department reference record (REST source).

    Schema version: department_reference.v1
    Identifiers:    code
    """

    model_config = ConfigDict(strict=False)

    SCHEMA_VERSION: ClassVar[str] = "department_reference.v1"
    IDENTIFIER_FIELDS: ClassVar[tuple[str, ...]] = ("code",)

    # ── Required, non-nullable ─────────────────────────────────────────────
    code: str
    """Short department code (e.g. 'HR', 'ENG').  Required.  Non-nullable."""

    name: str
    """Human-readable department name.  Required.  Non-nullable."""

"""Standardization layer for the Enterprise Data Pipeline.

Standardization converts heterogeneous source representations into a common
internal structure per entity.  It runs on RawRecord objects produced by the
RAW layer.

Pipeline position:
    RAW  (app/pipelines/raw.py)
      ↓
    STANDARDIZATION  ← this module
      ↓
    [next: Data Quality]

What standardization DOES:
  - Normalises field names to a consistent internal name
  - Converts string timestamps to datetime objects (structural, not business)
  - Strips leading/trailing whitespace from string values
  - Converts empty strings to None (consistent null representation)
  - Ensures consistent Python types across source formats

What standardization does NOT do:
  - Validate business rules (e.g., "is this a valid status value?")
  - Reject records that are business-invalid
  - Check referential integrity (e.g., "does this employee_id exist?")
  - Detect duplicates
  - Repair "INVALID-DATE" strings — a string that cannot be parsed remains None
    but the record is still passed on; the Data Quality stage decides what to do.

Entity-level mapping:
    employees.csv / employees.json / employees.parquet / PG employees table
          → StandardizedEmployee

    cases.csv / cases.json / cases.parquet
          → StandardizedCase

    case_history.csv / case_history.json / case_history.parquet
          → StandardizedCaseHistory

    REST /departments
          → StandardizedDepartmentReference
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.pipelines.raw import RawRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_or_none(value: Any) -> str | None:
    """Return stripped string, or None if value is None/empty."""
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped if stripped else None


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime string into a timezone-aware datetime object.

    Accepts ISO-8601 strings (with or without timezone offset).
    Returns None — without raising — if the value cannot be parsed.
    The Data Quality stage is responsible for deciding whether a missing
    datetime is an error.

    Args:
        value: A string, datetime, or None.

    Returns:
        A timezone-aware datetime, or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        # Already a datetime (e.g. from PostgreSQL driver) — ensure tz-aware.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        # Python 3.11+ fromisoformat handles offsets; for 3.9-3.10 we need a shim.
        parsed = datetime.fromisoformat(str(value).strip())
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        logger.debug("Could not parse datetime value: %r — leaving as None", value)
        return None


# ---------------------------------------------------------------------------
# Standardized entity dataclasses
# ---------------------------------------------------------------------------

@dataclass
class StandardizedEmployee:
    """Common internal representation for an employee record.

    Field mapping (source → standard):
        employee_id  → employee_id    (no rename — source already canonical)
        name         → name
        email        → email
        department   → department
        job_title    → job_title
        status       → status
        created_at   → created_at    (datetime)
        updated_at   → updated_at    (datetime)

    Metadata:
        _raw_run_id       : run_id from the originating RawRecord
        _raw_source_system: source_system from the originating RawRecord
    """
    employee_id: str | None
    name: str | None
    email: str | None
    department: str | None
    job_title: str | None
    status: str | None
    created_at: datetime | None
    updated_at: datetime | None
    # Pipeline traceability — not a business field
    _raw_run_id: str = ""
    _raw_source_system: str = ""


@dataclass
class StandardizedCase:
    """Common internal representation for a case record."""
    case_id: str | None
    employee_id: str | None
    category: str | None
    subject: str | None
    description: str | None
    status: str | None
    priority: str | None
    created_at: datetime | None
    updated_at: datetime | None
    _raw_run_id: str = ""
    _raw_source_system: str = ""


@dataclass
class StandardizedCaseHistory:
    """Common internal representation for a case history record."""
    history_id: str | None
    case_id: str | None
    old_status: str | None
    new_status: str | None
    comment: str | None
    changed_by: str | None
    created_at: datetime | None
    _raw_run_id: str = ""
    _raw_source_system: str = ""


@dataclass
class StandardizedDepartmentReference:
    """Common internal representation for department reference data (from REST)."""
    code: str | None
    name: str | None
    _raw_run_id: str = ""
    _raw_source_system: str = ""


# ---------------------------------------------------------------------------
# Standardization error
# ---------------------------------------------------------------------------

class StandardizationError(Exception):
    """Raised when a RawRecord cannot be structurally standardized.

    This is distinct from a Data Quality failure:
      - StandardizationError = the record structure is completely unexpected
        (e.g. wrong entity type, missing required structural field)
      - Data Quality failure = the record structure is valid but the values
        are business-invalid (handled by the later DQ stage)
    """


# ---------------------------------------------------------------------------
# Entity-specific standardizers
# ---------------------------------------------------------------------------

def standardize_employee(raw: RawRecord) -> StandardizedEmployee:
    """Convert a RawRecord containing employee data to StandardizedEmployee.

    Structural normalizations applied:
      - All string fields are stripped and empty → None
      - created_at / updated_at parsed to tz-aware datetime (None if unparseable)

    Args:
        raw: A RawRecord whose payload represents one employee.

    Returns:
        StandardizedEmployee

    Raises:
        StandardizationError: If the payload is not a dict.
    """
    p = raw.payload
    if not isinstance(p, dict):
        raise StandardizationError(
            f"Expected a dict payload for employee, got {type(p).__name__}"
        )

    logger.debug(
        "Standardizing employee | run_id=%s source=%s",
        raw.run_id,
        raw.source_system,
    )

    return StandardizedEmployee(
        employee_id=_strip_or_none(p.get("employee_id")),
        name=_strip_or_none(p.get("name")),
        email=_strip_or_none(p.get("email")),
        department=_strip_or_none(p.get("department")),
        job_title=_strip_or_none(p.get("job_title")),
        status=_strip_or_none(p.get("status")),
        created_at=_parse_datetime(p.get("created_at")),
        updated_at=_parse_datetime(p.get("updated_at")),
        _raw_run_id=raw.run_id,
        _raw_source_system=raw.source_system,
    )


def standardize_case(raw: RawRecord) -> StandardizedCase:
    """Convert a RawRecord containing case data to StandardizedCase."""
    p = raw.payload
    if not isinstance(p, dict):
        raise StandardizationError(
            f"Expected a dict payload for case, got {type(p).__name__}"
        )

    return StandardizedCase(
        case_id=_strip_or_none(p.get("case_id")),
        employee_id=_strip_or_none(p.get("employee_id")),
        category=_strip_or_none(p.get("category")),
        subject=_strip_or_none(p.get("subject")),
        description=_strip_or_none(p.get("description")),
        status=_strip_or_none(p.get("status")),
        priority=_strip_or_none(p.get("priority")),
        created_at=_parse_datetime(p.get("created_at")),
        updated_at=_parse_datetime(p.get("updated_at")),
        _raw_run_id=raw.run_id,
        _raw_source_system=raw.source_system,
    )


def standardize_case_history(raw: RawRecord) -> StandardizedCaseHistory:
    """Convert a RawRecord containing case history data to StandardizedCaseHistory."""
    p = raw.payload
    if not isinstance(p, dict):
        raise StandardizationError(
            f"Expected a dict payload for case_history, got {type(p).__name__}"
        )

    return StandardizedCaseHistory(
        history_id=_strip_or_none(p.get("history_id")),
        case_id=_strip_or_none(p.get("case_id")),
        old_status=_strip_or_none(p.get("old_status")),
        new_status=_strip_or_none(p.get("new_status")),
        comment=_strip_or_none(p.get("comment")),
        changed_by=_strip_or_none(p.get("changed_by")),
        created_at=_parse_datetime(p.get("created_at")),
        _raw_run_id=raw.run_id,
        _raw_source_system=raw.source_system,
    )


def standardize_department_reference(raw: RawRecord) -> StandardizedDepartmentReference:
    """Convert a RawRecord containing REST department reference data."""
    p = raw.payload
    if not isinstance(p, dict):
        raise StandardizationError(
            f"Expected a dict payload for department_reference, got {type(p).__name__}"
        )

    return StandardizedDepartmentReference(
        code=_strip_or_none(p.get("code")),
        name=_strip_or_none(p.get("name")),
        _raw_run_id=raw.run_id,
        _raw_source_system=raw.source_system,
    )


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------

def standardize_employees(raw_records: list[RawRecord]) -> list[StandardizedEmployee]:
    """Standardize a batch of employee RawRecords."""
    results = []
    for raw in raw_records:
        try:
            results.append(standardize_employee(raw))
        except StandardizationError as e:
            logger.error("Employee standardization failed: %s | payload=%r", e, raw.payload)
            raise
    logger.info(
        "Standardization complete | entity=employee records=%d", len(results)
    )
    return results


def standardize_cases(raw_records: list[RawRecord]) -> list[StandardizedCase]:
    """Standardize a batch of case RawRecords."""
    results = []
    for raw in raw_records:
        try:
            results.append(standardize_case(raw))
        except StandardizationError as e:
            logger.error("Case standardization failed: %s | payload=%r", e, raw.payload)
            raise
    logger.info("Standardization complete | entity=case records=%d", len(results))
    return results


def standardize_case_histories(
    raw_records: list[RawRecord],
) -> list[StandardizedCaseHistory]:
    """Standardize a batch of case history RawRecords."""
    results = []
    for raw in raw_records:
        try:
            results.append(standardize_case_history(raw))
        except StandardizationError as e:
            logger.error(
                "CaseHistory standardization failed: %s | payload=%r", e, raw.payload
            )
            raise
    logger.info(
        "Standardization complete | entity=case_history records=%d", len(results)
    )
    return results


def standardize_department_references(
    raw_records: list[RawRecord],
) -> list[StandardizedDepartmentReference]:
    """Standardize a batch of department reference RawRecords."""
    results = []
    for raw in raw_records:
        try:
            results.append(standardize_department_reference(raw))
        except StandardizationError as e:
            logger.error(
                "DepartmentReference standardization failed: %s | payload=%r",
                e,
                raw.payload,
            )
            raise
    logger.info(
        "Standardization complete | entity=department_reference records=%d", len(results)
    )
    return results

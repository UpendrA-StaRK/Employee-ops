"""Schema validation layer for the Employee Operations pipeline.

This module validates standardized entity records against their declared
canonical schemas.  It sits between the standardization layer and the
future Data Quality layer.

Pipeline position:
    STANDARDIZATION  (app/pipelines/standardize.py)
      ↓
    SCHEMA VALIDATION  ← this module
      ↓
    DATA QUALITY  (Part 6 — not yet implemented)

What schema validation DOES check:
  - Required fields are present (employee_id, case_id, etc.)
  - Field types match the canonical schema (str, datetime | None, etc.)
  - Nullable fields accept None
  - Schema version is identifiable on the result

What schema validation does NOT check (Part 6 — Data Quality):
  - Whether a required field's *value* is business-valid
    (e.g. employee_id is a string ✓ but does not correspond to a real employee ✗)
  - Enum membership (e.g. status in {'OPEN','CLOSED','IN_PROGRESS',...})
  - Referential integrity (FK relationships)
  - Business rules (hire_date before today, etc.)
  - Duplicate detection

Failure handling
----------------
Schema validation failures are explicit and logged.  They are NOT silently
swallowed.

A ``SchemaValidationError`` is raised for every hard mismatch (missing required
field, incompatible type).  This is distinct from ``StandardizationError``:

    StandardizationError  — structural failure during standardization
                            (e.g. payload is not a dict at all)

    SchemaValidationError — the standardized record does not conform to
                            its declared canonical schema

The two exceptions are deliberately separate classes; catching one does not
catch the other.

Usage example:
    from app.pipelines.standardize import standardize_employee
    from app.pipelines.schemas.validator import validate_employee, SchemaValidationError

    standardized = standardize_employee(raw_record)
    result = validate_employee(standardized)        # raises on hard failure
    if result.is_valid:
        ...  # pass to Data Quality
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.pipelines.schemas.canonical import (
    CaseHistorySchemaV1,
    CaseSchemaV1,
    DepartmentReferenceSchemaV1,
    EmployeeSchemaV1,
)
from app.pipelines.standardize import (
    StandardizedCase,
    StandardizedCaseHistory,
    StandardizedDepartmentReference,
    StandardizedEmployee,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class SchemaValidationError(Exception):
    """Raised when a standardized record does not conform to its canonical schema.

    This is distinct from StandardizationError (which signals a structural
    failure during the standardization step itself).

    Attributes:
        entity:         Entity name (e.g. "employee").
        schema_version: Schema version string (e.g. "employee.v1").
        errors:         List of human-readable validation error descriptions.
    """

    def __init__(
        self,
        message: str,
        *,
        entity: str,
        schema_version: str,
        errors: list[str],
    ) -> None:
        super().__init__(message)
        self.entity = entity
        self.schema_version = schema_version
        self.errors = errors

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"SchemaValidationError(entity={self.entity!r}, "
            f"schema_version={self.schema_version!r}, "
            f"errors={self.errors!r})"
        )


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class SchemaValidationResult:
    """Result returned by every validate_* function.

    Attributes:
        is_valid:       True if the record conforms to the schema.
        entity:         Entity name (e.g. "employee").
        schema_version: Schema version string used for validation.
        errors:         Empty list on success; human-readable descriptions on failure.
    """

    is_valid: bool
    entity: str
    schema_version: str
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a standardized dataclass to a plain dict, excluding pipeline
    traceability fields (those starting with '_')."""
    return {
        k: v
        for k, v in obj.__dict__.items()
        if not k.startswith("_")
    }


def _validate_against_schema(
    record_dict: dict[str, Any],
    schema_class: type,
    entity: str,
    schema_version: str,
) -> SchemaValidationResult:
    """Core validation logic: feed the dict into a Pydantic schema model.

    Pydantic v2's model_validate() raises ValidationError on:
      - missing required fields
      - incompatible types

    Returns a SchemaValidationResult. Raises SchemaValidationError for any
    validation failure.
    """
    try:
        schema_class.model_validate(record_dict)
    except ValidationError as exc:
        # Extract human-readable error descriptions from Pydantic
        errors = [
            f"field={e['loc'][0]!r} | type={e['type']} | msg={e['msg']}"
            for e in exc.errors()
        ]
        logger.error(
            "Schema validation failed | entity=%s schema_version=%s errors=%s",
            entity,
            schema_version,
            errors,
        )
        raise SchemaValidationError(
            f"Record does not conform to schema {schema_version!r}: {errors}",
            entity=entity,
            schema_version=schema_version,
            errors=errors,
        ) from exc

    logger.debug(
        "Schema validation passed | entity=%s schema_version=%s",
        entity,
        schema_version,
    )
    return SchemaValidationResult(
        is_valid=True,
        entity=entity,
        schema_version=schema_version,
        errors=[],
    )


# ---------------------------------------------------------------------------
# Public validators
# ---------------------------------------------------------------------------

def validate_employee(record: StandardizedEmployee) -> SchemaValidationResult:
    """Validate a StandardizedEmployee against EmployeeSchemaV1.

    Args:
        record: A StandardizedEmployee produced by standardize_employee().

    Returns:
        SchemaValidationResult with is_valid=True on success.

    Raises:
        SchemaValidationError: If the record does not conform to employee.v1.
    """
    return _validate_against_schema(
        _dataclass_to_dict(record),
        EmployeeSchemaV1,
        entity="employee",
        schema_version=EmployeeSchemaV1.SCHEMA_VERSION,
    )


def validate_case(record: StandardizedCase) -> SchemaValidationResult:
    """Validate a StandardizedCase against CaseSchemaV1.

    Args:
        record: A StandardizedCase produced by standardize_case().

    Returns:
        SchemaValidationResult with is_valid=True on success.

    Raises:
        SchemaValidationError: If the record does not conform to case.v1.
    """
    return _validate_against_schema(
        _dataclass_to_dict(record),
        CaseSchemaV1,
        entity="case",
        schema_version=CaseSchemaV1.SCHEMA_VERSION,
    )


def validate_case_history(record: StandardizedCaseHistory) -> SchemaValidationResult:
    """Validate a StandardizedCaseHistory against CaseHistorySchemaV1.

    Args:
        record: A StandardizedCaseHistory produced by standardize_case_history().

    Returns:
        SchemaValidationResult with is_valid=True on success.

    Raises:
        SchemaValidationError: If the record does not conform to case_history.v1.
    """
    return _validate_against_schema(
        _dataclass_to_dict(record),
        CaseHistorySchemaV1,
        entity="case_history",
        schema_version=CaseHistorySchemaV1.SCHEMA_VERSION,
    )


def validate_department_reference(
    record: StandardizedDepartmentReference,
) -> SchemaValidationResult:
    """Validate a StandardizedDepartmentReference against DepartmentReferenceSchemaV1.

    Args:
        record: A StandardizedDepartmentReference produced by standardize_department_reference().

    Returns:
        SchemaValidationResult with is_valid=True on success.

    Raises:
        SchemaValidationError: If the record does not conform to department_reference.v1.
    """
    return _validate_against_schema(
        _dataclass_to_dict(record),
        DepartmentReferenceSchemaV1,
        entity="department_reference",
        schema_version=DepartmentReferenceSchemaV1.SCHEMA_VERSION,
    )

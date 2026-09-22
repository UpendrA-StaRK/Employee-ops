"""Data contract definitions for the Employee Operations pipeline.

A **data contract** defines the explicit expectations between a data producer
(source system) and the consuming pipeline stage.

A contract references a canonical schema version and adds:
  - producer identity (which source provides the data)
  - consumer identity (which pipeline stage consumes it)
  - required field list (what the producer must supply)
  - field type descriptions (human-readable, for documentation/auditing)
  - identifier fields (what uniquely identifies a record)
  - compatibility rules (what schema changes are safe vs breaking)

Contracts do NOT duplicate schema field definitions redundantly — they
reference the schema version and add the producer/consumer context.

Relationship:

    DATA CONTRACT
        references
            ↓
        SCHEMA VERSION  (defined in canonical.py)

Module-level contract constants
--------------------------------
    EMPLOYEE_CONTRACT
    CASE_CONTRACT
    CASE_HISTORY_CONTRACT
    DEPARTMENT_REFERENCE_CONTRACT
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.pipelines.schemas.canonical import (
    CaseHistorySchemaV1,
    CaseSchemaV1,
    DepartmentReferenceSchemaV1,
    EmployeeSchemaV1,
)


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompatibilityRules:
    """Documents what kinds of schema changes are safe vs potentially breaking.

    These rules express deliberate intent about schema evolution.  They are
    informational/documentary rather than enforced automatically — enforcement
    belongs to a future schema-registry or CI check.

    Attributes:
        compatible_changes:   Changes that should not break existing consumers.
        breaking_changes:     Changes that would require coordinated migration.
    """

    compatible_changes: tuple[str, ...]
    breaking_changes: tuple[str, ...]


@dataclass(frozen=True)
class DataContract:
    """An explicit contract between a data producer and the pipeline consumer.

    Attributes:
        name:              Human-readable contract name.
        producer:          Source system that produces the data.
        consumer:          Pipeline stage that consumes the data.
        entity:            Business entity this contract covers.
        schema_version:    Canonical schema version identifier (e.g. "employee.v1").
        identifier_fields: Fields that uniquely identify a record of this entity.
        required_fields:   Fields the producer must supply (schema-level requirement).
        field_types:       Mapping of field name → human-readable type description.
        compatibility:     Rules governing safe vs breaking schema evolution.
    """

    name: str
    producer: str
    consumer: str
    entity: str
    schema_version: str
    identifier_fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    field_types: dict[str, str]
    compatibility: CompatibilityRules


# ---------------------------------------------------------------------------
# Shared compatibility rules
# ---------------------------------------------------------------------------

_STANDARD_COMPATIBILITY = CompatibilityRules(
    compatible_changes=(
        "Adding a new optional field with a nullable type",
        "Adding a new nullable field to the schema",
        "Widening a field type (e.g. str → str | None) where consumers tolerate None",
    ),
    breaking_changes=(
        "Removing a required field",
        "Renaming an identifier field (employee_id, case_id, history_id, code)",
        "Changing a field type incompatibly (e.g. str → int)",
        "Making a nullable field non-nullable when producers may omit it",
        "Changing identifier field semantics",
        "Removing a field that downstream consumers depend on",
    ),
)


# ---------------------------------------------------------------------------
# Employee contract
# ---------------------------------------------------------------------------

EMPLOYEE_CONTRACT = DataContract(
    name="Employee Source Contract",
    producer="employee_source (CSV / JSON / Parquet / PostgreSQL)",
    consumer="Employee Operations pipeline — standardization + schema validation",
    entity="Employee",
    schema_version=EmployeeSchemaV1.SCHEMA_VERSION,          # "employee.v1"
    identifier_fields=EmployeeSchemaV1.IDENTIFIER_FIELDS,    # ("employee_id",)
    required_fields=(
        "employee_id",
        "name",
        "email",
        "department",
        "job_title",
        "status",
        "created_at",
        "updated_at",
    ),
    field_types={
        "employee_id": "str — non-nullable UUID string",
        "name":        "str — non-nullable full name",
        "email":       "str — non-nullable email address",
        "department":  "str | None — department name, nullable",
        "job_title":   "str | None — job title, nullable",
        "status":      "str | None — employment status string, nullable",
        "created_at":  "datetime | None — tz-aware UTC datetime, nullable",
        "updated_at":  "datetime | None — tz-aware UTC datetime, nullable",
    },
    compatibility=_STANDARD_COMPATIBILITY,
)


# ---------------------------------------------------------------------------
# Case contract
# ---------------------------------------------------------------------------

CASE_CONTRACT = DataContract(
    name="Case Source Contract",
    producer="case_source (CSV / JSON / Parquet)",
    consumer="Employee Operations pipeline — standardization + schema validation",
    entity="Case",
    schema_version=CaseSchemaV1.SCHEMA_VERSION,           # "case.v1"
    identifier_fields=CaseSchemaV1.IDENTIFIER_FIELDS,     # ("case_id",)
    required_fields=(
        "case_id",
        "employee_id",
        "category",
        "subject",
        "description",
        "status",
        "priority",
        "created_at",
        "updated_at",
    ),
    field_types={
        "case_id":     "str — non-nullable UUID string",
        "employee_id": "str — non-nullable UUID string (FK to employee)",
        "category":    "str | None — case category string, nullable",
        "subject":     "str | None — short subject text, nullable",
        "description": "str | None — full description text, nullable",
        "status":      "str | None — case lifecycle status string, nullable",
        "priority":    "str | None — priority string, nullable",
        "created_at":  "datetime | None — tz-aware UTC datetime, nullable",
        "updated_at":  "datetime | None — tz-aware UTC datetime, nullable",
    },
    compatibility=_STANDARD_COMPATIBILITY,
)


# ---------------------------------------------------------------------------
# CaseHistory contract
# ---------------------------------------------------------------------------

CASE_HISTORY_CONTRACT = DataContract(
    name="Case History Source Contract",
    producer="case_history_source (CSV / JSON / Parquet)",
    consumer="Employee Operations pipeline — standardization + schema validation",
    entity="CaseHistory",
    schema_version=CaseHistorySchemaV1.SCHEMA_VERSION,          # "case_history.v1"
    identifier_fields=CaseHistorySchemaV1.IDENTIFIER_FIELDS,    # ("history_id",)
    required_fields=(
        "history_id",
        "case_id",
        "old_status",
        "new_status",
        "changed_by",
        "created_at",
    ),
    field_types={
        "history_id": "str — non-nullable UUID string",
        "case_id":    "str — non-nullable UUID string (FK to case)",
        "old_status": "str | None — previous case status; None for initial record",
        "new_status": "str — non-nullable target case status",
        "comment":    "str | None — optional annotation, nullable",
        "changed_by": "str | None — actor identifier, nullable",
        "created_at": "datetime | None — tz-aware UTC datetime, nullable",
    },
    compatibility=_STANDARD_COMPATIBILITY,
)


# ---------------------------------------------------------------------------
# DepartmentReference contract
# ---------------------------------------------------------------------------

DEPARTMENT_REFERENCE_CONTRACT = DataContract(
    name="Department Reference Source Contract",
    producer="rest_departments (REST API /departments endpoint)",
    consumer="Employee Operations pipeline — standardization + schema validation",
    entity="DepartmentReference",
    schema_version=DepartmentReferenceSchemaV1.SCHEMA_VERSION,        # "department_reference.v1"
    identifier_fields=DepartmentReferenceSchemaV1.IDENTIFIER_FIELDS,  # ("code",)
    required_fields=(
        "code",
        "name",
    ),
    field_types={
        "code": "str — non-nullable department code (e.g. 'HR', 'ENG')",
        "name": "str — non-nullable human-readable department name",
    },
    compatibility=_STANDARD_COMPATIBILITY,
)

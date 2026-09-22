"""Canonical schema and data-contract layer for the Enterprise Data Pipeline.

Pipeline position:
    RAW
      ↓
    STANDARDIZATION  (app/pipelines/standardize.py)
      ↓
    SCHEMA VALIDATION  ← this package
      ↓
    DATA QUALITY  (Part 6 — not yet implemented)

Public API
----------
Canonical schemas (Pydantic models):
    EmployeeSchemaV1
    CaseSchemaV1
    CaseHistorySchemaV1
    DepartmentReferenceSchemaV1

Data contracts (frozen dataclasses):
    EMPLOYEE_CONTRACT
    CASE_CONTRACT
    CASE_HISTORY_CONTRACT
    DEPARTMENT_REFERENCE_CONTRACT

Validation:
    SchemaValidationError
    SchemaValidationResult
    validate_employee
    validate_case
    validate_case_history
    validate_department_reference
"""

from app.pipelines.schemas.canonical import (
    CaseHistorySchemaV1,
    CaseSchemaV1,
    DepartmentReferenceSchemaV1,
    EmployeeSchemaV1,
)
from app.pipelines.schemas.contracts import (
    CASE_CONTRACT,
    CASE_HISTORY_CONTRACT,
    DEPARTMENT_REFERENCE_CONTRACT,
    EMPLOYEE_CONTRACT,
    CompatibilityRules,
    DataContract,
)
from app.pipelines.schemas.validator import (
    SchemaValidationError,
    SchemaValidationResult,
    validate_case,
    validate_case_history,
    validate_department_reference,
    validate_employee,
)

__all__ = [
    # Canonical schemas
    "EmployeeSchemaV1",
    "CaseSchemaV1",
    "CaseHistorySchemaV1",
    "DepartmentReferenceSchemaV1",
    # Data contracts
    "EMPLOYEE_CONTRACT",
    "CASE_CONTRACT",
    "CASE_HISTORY_CONTRACT",
    "DEPARTMENT_REFERENCE_CONTRACT",
    "DataContract",
    "CompatibilityRules",
    # Validation
    "SchemaValidationError",
    "SchemaValidationResult",
    "validate_employee",
    "validate_case",
    "validate_case_history",
    "validate_department_reference",
]

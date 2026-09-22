"""Data Quality and Rejected Records layer for the Enterprise Data Pipeline.

This package evaluates standardized/schema-valid records against record-level
business rules. Records that fail are routed to a Quarantine storage, while
valid records continue downstream.

Pipeline position:
    SCHEMA VALIDATION  (app/pipelines/schemas/)
      ↓
    DATA QUALITY  ← this package
      ├── VALID
      │     ↓
      │   downstream processing
      │
      └── INVALID
            ↓
         REJECTED / QUARANTINE

Public API
----------
Engine & Core:
    DataQualityEngine
    QualityContext
    QualityResult
    RuleFailure
    RejectedRecord
    persist_rejected

Rules:
    QualityRule (Protocol)
    RequiredBusinessValueRule
    AllowedEnumRule
    EmailFormatRule
    UniqueEmployeeIdRule
    EmployeeReferenceRule
"""

from app.pipelines.quality.engine import (
    DataQualityEngine,
    QualityContext,
    QualityResult,
    RuleFailure,
)
from app.pipelines.quality.rejection import (
    RejectedRecord,
    persist_rejected,
)
from app.pipelines.quality.rules import (
    AllowedEnumRule,
    EmailFormatRule,
    EmployeeReferenceRule,
    QualityRule,
    RequiredBusinessValueRule,
    UniqueEmployeeIdRule,
)

__all__ = [
    # Engine & Core
    "DataQualityEngine",
    "QualityContext",
    "QualityResult",
    "RuleFailure",
    "RejectedRecord",
    "persist_rejected",
    # Rules
    "QualityRule",
    "RequiredBusinessValueRule",
    "AllowedEnumRule",
    "EmailFormatRule",
    "UniqueEmployeeIdRule",
    "EmployeeReferenceRule",
]

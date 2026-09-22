"""Data Quality Rules Implementation.

Defines a `QualityRule` base protocol and specific implementations across
different data quality dimensions (Completeness, Validity, Uniqueness,
Referential Integrity).
"""
from __future__ import annotations

import re
from typing import Any, Protocol

from app.pipelines.quality.engine import QualityContext, RuleFailure


class QualityRule(Protocol):
    """Protocol for all data quality rules."""

    @property
    def name(self) -> str:
        """Name of the rule (e.g. 'UniqueEmployeeIdRule')."""
        ...

    @property
    def dimension(self) -> str:
        """Quality dimension (e.g. 'Uniqueness', 'Validity')."""
        ...

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        """Evaluate a standardized record against this rule.

        Args:
            record:  The standardized entity (e.g. StandardizedEmployee).
            context: Shared context for batch validation (tracking seen IDs, etc.).

        Returns:
            RuleFailure if the record violates the rule, else None.
        """
        ...


# ---------------------------------------------------------------------------
# Completeness Rules
# ---------------------------------------------------------------------------

class RequiredBusinessValueRule:
    """Ensures a schema-nullable field is present for business validity.

    While the standardizer and schema may allow a field to be None (e.g. an
    unparseable date, or empty string department), the business requires it
    to be populated.
    """
    dimension = "Completeness"

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.name = f"RequiredBusinessValueRule_{field_name}"

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        value = getattr(record, self.field_name, None)
        if value is None:
            return RuleFailure(
                rule_name=self.name,
                dimension=self.dimension,
                field=self.field_name,
                message=f"Required business field '{self.field_name}' is missing or None.",
            )
        return None


# ---------------------------------------------------------------------------
# Validity Rules
# ---------------------------------------------------------------------------

class AllowedEnumRule:
    """Validates that a string value belongs to a predefined set of allowed values."""
    dimension = "Validity"

    def __init__(self, field_name: str, allowed_values: set[str]):
        self.field_name = field_name
        self.allowed_values = allowed_values
        self.name = f"AllowedEnumRule_{field_name}"

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        value = getattr(record, self.field_name, None)
        if value is None:
            # Nulls should be caught by Completeness rules if they are required.
            return None
            
        if value not in self.allowed_values:
            return RuleFailure(
                rule_name=self.name,
                dimension=self.dimension,
                field=self.field_name,
                message=f"Value '{value}' is not in allowed set for '{self.field_name}'.",
            )
        return None


class EmailFormatRule:
    """Validates that an email string looks roughly like an email."""
    dimension = "Validity"
    name = "EmailFormatRule"
    
    _EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    def __init__(self, field_name: str = "email"):
        self.field_name = field_name

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        value = getattr(record, self.field_name, None)
        if value is None:
            return None
            
        if not isinstance(value, str) or not self._EMAIL_REGEX.match(value):
            return RuleFailure(
                rule_name=self.name,
                dimension=self.dimension,
                field=self.field_name,
                message=f"Invalid email format: '{value}'.",
            )
        return None


# ---------------------------------------------------------------------------
# Uniqueness Rules
# ---------------------------------------------------------------------------

class UniqueEmployeeIdRule:
    """Ensures employee IDs are unique within the processed batch."""
    dimension = "Uniqueness"
    name = "UniqueEmployeeIdRule"

    def __init__(self, field_name: str = "employee_id"):
        self.field_name = field_name

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        value = getattr(record, self.field_name, None)
        if value is None:
            return None
            
        if value in context.seen_employee_ids:
            return RuleFailure(
                rule_name=self.name,
                dimension=self.dimension,
                field=self.field_name,
                message=f"Duplicate identifier '{value}' found in batch.",
            )
            
        # Add to seen set if this is the first time
        context.seen_employee_ids.add(value)
        return None


# ---------------------------------------------------------------------------
# Referential Integrity Rules
# ---------------------------------------------------------------------------

class EmployeeReferenceRule:
    """Ensures a foreign key refers to a known employee ID."""
    dimension = "Referential Integrity"
    name = "EmployeeReferenceRule"

    def __init__(self, field_name: str = "employee_id"):
        self.field_name = field_name

    def evaluate(self, record: Any, context: QualityContext) -> RuleFailure | None:
        value = getattr(record, self.field_name, None)
        if value is None:
            return None
            
        # If the context is empty or uninitialized for known IDs, we skip validation
        # (or depending on architecture, we might fail. Assuming if provided, it must match).
        if context.known_employee_ids and value not in context.known_employee_ids:
            return RuleFailure(
                rule_name=self.name,
                dimension=self.dimension,
                field=self.field_name,
                message=f"Reference '{value}' not found in known employee IDs.",
            )
        return None

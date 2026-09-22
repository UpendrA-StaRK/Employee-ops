"""Data Quality Engine.

Evaluates standardized/schema-valid records against a set of quality rules,
separating the valid records from the rejected ones.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, TYPE_CHECKING

from app.pipelines.quality.rejection import RejectedRecord

if TYPE_CHECKING:
    from app.pipelines.quality.rules import QualityRule

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RuleFailure:
    """Represents a single data quality rule failure."""
    rule_name: str
    dimension: str
    field: str
    message: str


@dataclass
class QualityContext:
    """Shared state for a batch of records during data quality evaluation.

    Allows rules that require cross-record or reference data (like uniqueness
    checks or referential integrity) to operate cleanly.
    """
    # Provided externally (e.g. from DB) before running validation on cases
    known_employee_ids: set[str] = field(default_factory=set)
    
    # Mutated by uniqueness rules during batch processing
    seen_employee_ids: set[str] = field(default_factory=set)


@dataclass
class QualityResult(Generic[T]):
    """The dual output of the Data Quality stage."""
    valid_records: list[T]
    rejected_records: list[RejectedRecord]


class DataQualityEngine:
    """Evaluates records against rules and routes them to valid or rejected."""

    def __init__(self, rules: list["QualityRule"]):
        """Initialize with a specific list of quality rules.
        
        Args:
            rules: The rules to evaluate against each record.
        """
        self.rules = rules

    def evaluate_batch(
        self,
        records: list[T],
        context: QualityContext,
        entity_name: str,
    ) -> QualityResult[T]:
        """Evaluate a batch of records.

        Args:
            records:     List of standardized records that passed schema validation.
            context:     The batch context for cross-record validation.
            entity_name: Business entity name (e.g. "Employee").

        Returns:
            QualityResult containing separated valid and rejected records.
        """
        valid: list[T] = []
        rejected: list[RejectedRecord] = []

        for record in records:
            failures: list[RuleFailure] = []
            
            # Record-level failures are caught and appended to failures list.
            # System-level exceptions (unhandled TypeError, etc.) are intentionally NOT
            # caught here; they will bubble up and fail the pipeline (Req #14).
            for rule in self.rules:
                failure = rule.evaluate(record, context)
                if failure:
                    failures.append(failure)

            if not failures:
                valid.append(record)
            else:
                # To capture the payload safely, we convert the dataclass to a dict.
                # Pipeline metadata fields (_raw_run_id) are kept to trace the rejection.
                payload = {k: v for k, v in record.__dict__.items()}
                
                # Extract run metadata
                run_id = getattr(record, "_raw_run_id", "unknown_run")
                source_system = getattr(record, "_raw_source_system", "unknown_source")

                rejected.append(
                    RejectedRecord(
                        entity=entity_name,
                        run_id=run_id,
                        source_system=source_system,
                        rejection_reasons=failures,
                        record_payload=payload,
                    )
                )

                logger.debug(
                    "Record rejected | entity=%s run_id=%s source=%s failures=%d",
                    entity_name,
                    run_id,
                    source_system,
                    len(failures),
                )

        logger.info(
            "Data Quality evaluation complete | entity=%s total=%d valid=%d rejected=%d",
            entity_name,
            len(records),
            len(valid),
            len(rejected),
        )

        return QualityResult(
            valid_records=valid,
            rejected_records=rejected,
        )

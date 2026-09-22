"""Count reconciliation for curated pipeline outputs.

Reconciliation checks explicit stage semantics.  It does not assume every
stage has equal counts: joining a case to one employee is many-to-one, while
the curated ``case_operations`` dataset intentionally remains one row per
case.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


class ReconciliationError(Exception):
    """Raised when a declared count invariant is violated."""


@dataclass(frozen=True)
class StageCounts:
    """Counts for one entity travelling through the current pipeline stages."""

    input_count: int
    standardized_count: int
    schema_valid_count: int
    rejected_count: int
    valid_count: int
    curated_count: int = 0

    @classmethod
    def from_quality_routing(
        cls,
        *,
        valid_count: int,
        rejected_count: int,
    ) -> "StageCounts":
        """Create current-boundary counts from Data Quality's dual output.

        Standardization and hard schema errors currently stop the pipeline, so
        every record presented to Data Quality is counted as input,
        standardized, and schema-valid at this boundary.
        """
        quality_input_count = valid_count + rejected_count
        return cls(
            input_count=quality_input_count,
            standardized_count=quality_input_count,
            schema_valid_count=quality_input_count,
            rejected_count=rejected_count,
            valid_count=valid_count,
        )


@dataclass(frozen=True)
class ReconciliationResult:
    """Reconciliation result stored in the run manifest."""

    entity: str
    counts: StageCounts
    invariants_checked: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready reconciliation data for the run manifest."""
        return {
            "entity": self.entity,
            "counts": asdict(self.counts),
            "invariants_checked": list(self.invariants_checked),
        }


def reconcile_quality_counts(*, entity: str, counts: StageCounts) -> ReconciliationResult:
    """Verify the quality-routing invariant for an entity.

    Schema validation currently raises on a hard mismatch, so all records that
    reach Data Quality are schema-valid.  Therefore only this invariant is
    asserted here: ``schema_valid_count == valid_count + rejected_count``.
    Earlier counts are captured for audit but are not forced equal, preserving
    room for legitimate future stage semantics.
    """
    if counts.schema_valid_count != counts.valid_count + counts.rejected_count:
        raise ReconciliationError(
            f"Quality reconciliation failed for {entity}: schema_valid_count "
            f"({counts.schema_valid_count}) must equal valid_count "
            f"({counts.valid_count}) + rejected_count ({counts.rejected_count})."
        )
    return ReconciliationResult(
        entity=entity,
        counts=counts,
        invariants_checked=(
            "schema_valid_count == valid_count + rejected_count",
        ),
    )


def reconcile_case_operations(counts: StageCounts) -> ReconciliationResult:
    """Verify quality routing and the one-row-per-valid-case curated grain."""
    reconcile_quality_counts(entity="case", counts=counts)
    if counts.curated_count != counts.valid_count:
        raise ReconciliationError(
            "Case operations reconciliation failed: curated_count "
            f"({counts.curated_count}) must equal valid case count "
            f"({counts.valid_count}) because the dataset grain is one row per case."
        )
    return ReconciliationResult(
        entity="case_operations",
        counts=counts,
        invariants_checked=(
            "schema_valid_count == valid_count + rejected_count",
            "curated_count == valid_count (one row per valid case)",
        ),
    )

"""Rejected Record Representation & Persistence.

This module provides the explicit representation for records that fail
Data Quality validation, and handles persisting them to a quarantine area.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.pipelines.quality.engine import RuleFailure

logger = logging.getLogger(__name__)

# Root directory for Quarantine/Rejected output. Override in tests if needed.
_DEFAULT_QUARANTINE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "quarantine"


@dataclass
class RejectedRecord:
    """Explicit representation of a record that failed data quality validation.

    A rejected record does not continue down the pipeline. It is routed here
    so it can be inspected, fixed, and potentially replayed later.

    Attributes:
        entity:            The business entity name (e.g. "Employee").
        run_id:            The pipeline run identifier.
        source_system:     The originating source system.
        rejection_reasons: A list of specific rule failures that caused rejection.
        record_payload:    The standardized record (dumped to a dictionary) that
                           failed validation.
        rejected_at:       UTC timestamp when the rejection occurred.
    """
    entity: str
    run_id: str
    source_system: str
    rejection_reasons: list[RuleFailure]
    record_payload: dict[str, Any]
    rejected_at: str = ""

    def __post_init__(self) -> None:
        if not self.rejected_at:
            self.rejected_at = datetime.now(timezone.utc).isoformat()


def persist_rejected(
    rejected_records: list[RejectedRecord],
    base_dir: Path | None = None,
) -> Path:
    """Write rejected records to disk as a JSON file in the Quarantine area.

    Output path: ``<base_dir>/<run_id>/<entity>_rejected.json``

    Uses the same file-based persistence pattern as the RAW layer, satisfying
    the architectural requirement without introducing new infrastructure.

    Args:
        rejected_records: List of records that failed DQ.
        base_dir:         Root directory for quarantine output. Defaults to
                          ``data/quarantine/`` relative to the repository root.

    Returns:
        Path to the written file.

    Raises:
        ValueError: If ``rejected_records`` is empty.
    """
    if not rejected_records:
        raise ValueError("No rejected records to persist.")

    root = base_dir or _DEFAULT_QUARANTINE_DIR
    # All records in the list should share the same run_id and entity
    run_id = rejected_records[0].run_id
    entity = rejected_records[0].entity

    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / f"{entity.lower()}_rejected.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in rejected_records], f, indent=2, default=str)

    logger.info(
        "Quarantined rejected records | path=%s records=%d",
        output_path,
        len(rejected_records),
    )
    return output_path

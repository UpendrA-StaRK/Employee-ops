"""Incremental + Idempotent Processing — Part 9.

This module implements the high-water-mark strategy for batch-oriented
incremental processing.  It operates on standardized records that have
already passed schema validation and data quality checks.

Pipeline position (conceptual):
    SOURCE
      ↓
    INCREMENTAL FILTER  ← select records newer than committed watermark
      ↓
    INGESTION / RAW / STANDARDIZE / SCHEMA / DQ / CURATED
      ↓
    RECONCILIATION
      ↓
    COMMIT WATERMARK   ← only on success

Incremental strategy
--------------------
Change field:
    ``StandardizedEmployee.updated_at`` — set at creation, updated on change.
    ``StandardizedCase.updated_at``    — same semantics.
    ``StandardizedCaseHistory.created_at`` — append-only; never updated.

Watermark kind:
    Composite ``(watermark_ts, watermark_id)`` to handle ties where multiple
    records share the same ``updated_at`` value.

Selection semantics (strict greater-than + tie-break):
    A record is included in the next incremental batch if:

        record.updated_at > watermark_ts
        OR
        (record.updated_at == watermark_ts AND record.entity_id > watermark_id)

    Records at EXACTLY the watermark boundary (both ts AND id equal) are
    EXCLUDED — they were already processed in the previous successful run.

Initial / full-load mode:
    When no committed watermark exists (``load_watermark`` returns ``None``),
    ALL records are selected.  The watermark is initialised to the maximum
    seen after the first successful run completes.

Watermark advancement rule:
    commit_watermark() MUST be called only after:
        1. Curated records are persisted to disk.
        2. Reconciliation passes.
        3. The run manifest is written with SUCCESS status.

    If any step fails, commit_watermark() is NOT called, and the next run
    retries from the last committed watermark.

Idempotency:
    File-based curated output (data/curated/{run_id}/case_operations.json)
    is written with open(..., "w"), which is inherently an overwrite.
    Reprocessing the same logical batch under the same run_id is safe.

    For future DB persistence (Part 10+), the correct strategy is
    INSERT ... ON CONFLICT (pk) DO UPDATE (upsert).

Late-arriving data:
    Timestamp-based watermarks cannot detect records whose ``updated_at`` is
    backdated after the watermark has advanced.  This is a known limitation.
    A small configurable lookback window can mitigate this at the cost of
    some reprocessing — idempotent persistence makes that safe.
    No window is implemented here; the limitation is documented.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, TypeVar

from sqlalchemy.orm import Session

from app.models.watermark import PipelineWatermark

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Composite watermark state
# ---------------------------------------------------------------------------

@dataclass
class IncrementalState:
    """Composite high-water-mark position for one incremental pipeline source.

    Attributes:
        pipeline_key:  Logical identifier for the source
                       (e.g. ``"employee_incremental"``).
        watermark_ts:  Timestamp component of the watermark.
        watermark_id:  Stable entity-id component (breaks timestamp ties).
    """
    pipeline_key: str
    watermark_ts: datetime
    watermark_id: str

    def __str__(self) -> str:
        return (
            f"IncrementalState(key={self.pipeline_key!r}, "
            f"ts={self.watermark_ts.isoformat()}, id={self.watermark_id!r})"
        )


# ---------------------------------------------------------------------------
# Protocol for selectable records
# ---------------------------------------------------------------------------

class _HasTimestampAndId(Protocol):
    """Structural protocol — any standardized entity with a change indicator."""
    updated_at: datetime | None
    # Every entity's identifier is accessed by name via getattr in the filter


# ---------------------------------------------------------------------------
# Pure in-memory record filter
# ---------------------------------------------------------------------------

def filter_records_by_watermark(
    records: list[T],
    *,
    state: IncrementalState | None,
    id_field: str,
    ts_field: str = "updated_at",
) -> tuple[list[T], IncrementalState | None]:
    """Select records that are newer than the committed watermark.

    This is a pure function — it does not touch the database.  It operates
    on already-standardized records (e.g. list[StandardizedEmployee]).

    Args:
        records:   List of standardized records.
        state:     The committed watermark state, or ``None`` for a full load.
        id_field:  The attribute name of the stable entity identifier
                   (e.g. ``"employee_id"``).
        ts_field:  The attribute name of the change-indicator timestamp
                   (default: ``"updated_at"``).

    Returns:
        A two-tuple:
          - ``selected``: records that pass the watermark filter (all records
            on full load; only newer records on incremental).
          - ``new_state``: an ``IncrementalState`` representing the new
            watermark that should be committed after successful processing,
            or ``None`` if no records were available.

    Notes:
        Records with a ``None`` timestamp are always included — they cannot
        be compared to a watermark, so they pass through.  The Data Quality
        layer has already accepted them as schema-valid; the business decision
        about missing timestamps belongs there, not here.
    """
    if not records:
        logger.info(
            "Incremental filter: no records to process | key=%s",
            state.pipeline_key if state else "full_load",
        )
        return [], None

    if state is None:
        # Full / initial load — select everything
        logger.info(
            "Incremental filter: full load mode | total_records=%d",
            len(records),
        )
        selected = records
    else:
        selected = []
        for record in records:
            record_ts: datetime | None = getattr(record, ts_field, None)
            record_id: str = getattr(record, id_field, "")

            if record_ts is None:
                # Cannot compare — include so DQ can decide
                selected.append(record)
                continue

            # Ensure timezone-aware comparison
            if record_ts.tzinfo is None:
                record_ts = record_ts.replace(tzinfo=timezone.utc)
            wm_ts = state.watermark_ts
            if wm_ts.tzinfo is None:
                wm_ts = wm_ts.replace(tzinfo=timezone.utc)

            if record_ts > wm_ts:
                selected.append(record)
            elif record_ts == wm_ts and record_id > state.watermark_id:
                # Tie-break: same timestamp, but higher entity id
                selected.append(record)
            # else: record is at or before the watermark — skip

        logger.info(
            "Incremental filter: incremental mode | key=%s "
            "total=%d selected=%d skipped=%d",
            state.pipeline_key,
            len(records),
            len(selected),
            len(records) - len(selected),
        )

    if not selected:
        return [], None

    # Calculate the new watermark from selected records
    new_ts: datetime | None = None
    new_id: str = ""
    for record in selected:
        record_ts = getattr(record, ts_field, None)
        record_id: str = getattr(record, id_field, "")
        if record_ts is None:
            continue
        if record_ts.tzinfo is None:
            record_ts = record_ts.replace(tzinfo=timezone.utc)
        if new_ts is None or record_ts > new_ts:
            new_ts = record_ts
            new_id = record_id
        elif record_ts == new_ts and record_id > new_id:
            new_id = record_id

    if new_ts is None:
        # All selected records had None timestamps — watermark unchanged
        return selected, state

    pipeline_key = state.pipeline_key if state else "unknown"
    new_state = IncrementalState(
        pipeline_key=pipeline_key,
        watermark_ts=new_ts,
        watermark_id=new_id,
    )
    return selected, new_state


# ---------------------------------------------------------------------------
# Database-backed watermark persistence
# ---------------------------------------------------------------------------

def load_watermark(
    pipeline_key: str,
    session: Session,
) -> IncrementalState | None:
    """Read the committed watermark for a pipeline source from the database.

    Args:
        pipeline_key: Logical identifier for the source.
        session:      An active SQLAlchemy session.

    Returns:
        ``IncrementalState`` if a committed watermark exists,
        ``None`` if this is the first run (triggers full load).
    """
    row: PipelineWatermark | None = session.get(PipelineWatermark, pipeline_key)
    if row is None:
        logger.info(
            "No committed watermark found — full load | key=%s", pipeline_key
        )
        return None

    state = IncrementalState(
        pipeline_key=pipeline_key,
        watermark_ts=(
            row.watermark_ts.replace(tzinfo=timezone.utc)
            if row.watermark_ts.tzinfo is None
            else row.watermark_ts
        ),
        watermark_id=row.watermark_id,
    )
    logger.info(
        "Loaded committed watermark | key=%s ts=%s id=%s",
        pipeline_key,
        row.watermark_ts.isoformat(),
        row.watermark_id,
    )
    return state


def commit_watermark(
    new_state: IncrementalState,
    session: Session,
) -> None:
    """Persist a new watermark to the database.

    This MUST be called only after:
        1. Curated records have been written to disk.
        2. Reconciliation has passed.
        3. The run manifest has been marked SUCCESS.

    On failure, do NOT call this function — the previous watermark remains
    committed and the next run will retry from there.

    Args:
        new_state: The watermark to commit.
        session:   An active SQLAlchemy session.  The caller is responsible
                   for committing the transaction after this call.
    """
    row: PipelineWatermark | None = session.get(
        PipelineWatermark, new_state.pipeline_key
    )
    now = datetime.now(timezone.utc)

    if row is None:
        # First-ever watermark for this source
        row = PipelineWatermark(
            pipeline_key=new_state.pipeline_key,
            watermark_ts=new_state.watermark_ts,
            watermark_id=new_state.watermark_id,
            updated_at=now,
        )
        session.add(row)
    else:
        row.watermark_ts = new_state.watermark_ts
        row.watermark_id = new_state.watermark_id
        row.updated_at = now

    logger.info(
        "Watermark committed | key=%s ts=%s id=%s",
        new_state.pipeline_key,
        new_state.watermark_ts.isoformat(),
        new_state.watermark_id,
    )
    # NOTE: caller must call session.commit() to make this durable.

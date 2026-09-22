"""Incremental processing watermark SQLAlchemy model.

This model persists the high-water-mark state for each incremental pipeline
source.  It is stored in PostgreSQL so that watermark advancement is an
atomic SQL UPDATE rather than a file-write that can be interrupted.

Pipeline position:
    This table is written AFTER successful curated persistence and
    reconciliation.  It is never updated when a run fails.

Table: pipeline_watermarks

Columns:
    pipeline_key  — e.g. ``"employee_incremental"``, ``"case_incremental"``
                    Primary key; one row per logical incremental source.
    watermark_ts  — The timestamp component of the composite watermark.
                    Represents ``max(updated_at)`` of the last successfully
                    processed batch.
    watermark_id  — The entity-id component of the composite watermark.
                    Represents the stable business key (employee_id, case_id)
                    at the ``watermark_ts`` boundary to handle ties.
    updated_at    — UTC timestamp of the last successful watermark commit.
                    Useful for audit; does not affect selection logic.

Composite watermark semantics:
    SELECT records WHERE
        (updated_at > watermark_ts)
        OR (updated_at = watermark_ts AND entity_id > watermark_id)
    ORDER BY updated_at ASC, entity_id ASC

This ensures no record at the boundary timestamp is skipped when multiple
records share the same ``updated_at`` value.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PipelineWatermark(Base):
    """Persistent high-water-mark state for one incremental pipeline source."""

    __tablename__ = "pipeline_watermarks"

    pipeline_key: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
        comment=(
            "Logical identifier for the incremental source, "
            "e.g. 'employee_incremental' or 'case_incremental'."
        ),
    )

    watermark_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment=(
            "Timestamp component of the composite high-water mark. "
            "Records with updated_at strictly greater than this value "
            "are selected in the next incremental run."
        ),
    )

    watermark_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        default="",
        comment=(
            "Entity-id component of the composite high-water mark. "
            "Used to break ties when multiple records share the same "
            "watermark_ts. Represents the stable business key "
            "(employee_id or case_id) at the boundary."
        ),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of the last successful watermark commit.",
    )

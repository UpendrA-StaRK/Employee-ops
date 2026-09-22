"""Minimal pipeline-run metadata and run-manifest persistence.

This is audit metadata for Parts 7 and 8 only.  It records what happened in a
single run; it intentionally contains no watermark, checkpoint, replay, or
idempotency state.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.pipelines.raw import create_run_id
from app.pipelines.reconciliation import ReconciliationResult, StageCounts
from app.pipelines.serialization import json_default

logger = logging.getLogger(__name__)

_DEFAULT_RUN_METADATA_DIR = Path(__file__).parent.parent.parent / "data" / "pipeline_runs"


class PipelineRunStatus(StrEnum):
    """Lifecycle states supported by a pipeline run manifest."""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclass
class PipelineRun:
    """Audit manifest for one independently identifiable pipeline run."""

    pipeline_name: str
    run_id: str = field(default_factory=create_run_id)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: PipelineRunStatus = PipelineRunStatus.RUNNING
    ended_at: datetime | None = None
    source_info: dict[str, Any] = field(default_factory=dict)
    entity_counts: dict[str, StageCounts] = field(default_factory=dict)
    reconciliation: list[ReconciliationResult] = field(default_factory=list)
    curated_output: str | None = None
    error_message: str | None = None

    def complete_success(
        self,
        *,
        entity_counts: dict[str, StageCounts],
        reconciliation: list[ReconciliationResult],
        curated_output: Path,
    ) -> None:
        """Mark the run successful only after curated persistence and reconciliation."""
        self.status = PipelineRunStatus.SUCCESS
        self.ended_at = datetime.now(timezone.utc)
        self.entity_counts = entity_counts
        self.reconciliation = reconciliation
        self.curated_output = str(curated_output)
        self.error_message = None

    def complete_failure(self, error: Exception) -> None:
        """Mark the run failed while preserving the reason for audit."""
        self.status = PipelineRunStatus.FAILURE
        self.ended_at = datetime.now(timezone.utc)
        self.error_message = str(error)


def persist_pipeline_run(
    pipeline_run: PipelineRun,
    *,
    base_dir: Path | None = None,
) -> Path:
    """Write the run manifest to ``data/pipeline_runs/<run_id>.json``."""
    root = base_dir or _DEFAULT_RUN_METADATA_DIR
    root.mkdir(parents=True, exist_ok=True)
    output_path = root / f"{pipeline_run.run_id}.json"

    payload = asdict(pipeline_run)
    payload["status"] = pipeline_run.status.value
    payload["reconciliation"] = [item.as_dict() for item in pipeline_run.reconciliation]
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, default=json_default)

    logger.info(
        "Pipeline run manifest persisted | run_id=%s status=%s path=%s",
        pipeline_run.run_id,
        pipeline_run.status,
        output_path,
    )
    return output_path

"""Parts 7+8 orchestration for the case-operations curated output.

This small coordinator starts and closes the audit run, but intentionally does
not absorb ingestion, standardization, schema validation, or data quality.
Its inputs are the ``QualityResult`` objects from Part 6, so only valid records
can reach the curated join.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.pipelines.curated import (
    CuratedCaseOperation,
    build_case_operations,
    persist_case_operations,
)
from app.pipelines.quality.engine import QualityResult
from app.pipelines.reconciliation import (
    ReconciliationResult,
    StageCounts,
    reconcile_case_operations,
    reconcile_quality_counts,
)
from app.pipelines.run_metadata import PipelineRun, persist_pipeline_run
from app.pipelines.standardize import StandardizedCase, StandardizedEmployee

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaseOperationsPipelineResult:
    """Successful result returned after output and its run manifest are persisted."""

    pipeline_run: PipelineRun
    curated_records: list[CuratedCaseOperation]
    curated_path: Path
    manifest_path: Path


def _counts_from_quality_result(result: QualityResult[Any]) -> StageCounts:
    """Build stage metrics using the record set received by Data Quality.

    At the current architecture boundary hard standardization or schema errors
    fail their run.  Therefore each record presented to Data Quality is both
    standardized and schema-valid; its cardinality is captured at all three
    stages.  Future orchestration can supply different stage counts when it
    introduces a valid transformation that changes them.
    """
    return StageCounts.from_quality_routing(
        valid_count=len(result.valid_records),
        rejected_count=len(result.rejected_records),
    )


def run_case_operations_pipeline(
    *,
    employee_quality: QualityResult[StandardizedEmployee],
    case_quality: QualityResult[StandardizedCase],
    pipeline_run: PipelineRun | None = None,
    source_info: dict[str, Any] | None = None,
    curated_base_dir: Path | None = None,
    run_metadata_base_dir: Path | None = None,
) -> CaseOperationsPipelineResult:
    """Create, reconcile, and persist the case-operations curated dataset.

    The caller may pass a pre-started ``PipelineRun`` (normally sharing the
    RAW run identifier) to preserve lineage across prior stages.  When absent,
    a fresh UUID run is created.  A failure is recorded in its manifest and then
    re-raised; it is never converted into a record-level rejection.
    """
    if pipeline_run is not None and source_info is not None:
        raise ValueError(
            "source_info cannot override a supplied PipelineRun; "
            "set it when constructing the run instead."
        )
    run = pipeline_run or PipelineRun(
        pipeline_name="case_operations_curated",
        source_info=source_info or {},
    )

    # A RUNNING manifest proves the run began even if later work fails.
    persist_pipeline_run(run, base_dir=run_metadata_base_dir)
    employee_counts = _counts_from_quality_result(employee_quality)
    case_counts = _counts_from_quality_result(case_quality)

    try:
        curated_records = build_case_operations(
            case_quality.valid_records,
            employee_quality.valid_records,
            pipeline_run_id=run.run_id,
        )
        case_counts = replace(case_counts, curated_count=len(curated_records))

        reconciliation: list[ReconciliationResult] = [
            reconcile_quality_counts(entity="employee", counts=employee_counts),
            reconcile_case_operations(case_counts),
        ]
        curated_path = persist_case_operations(
            curated_records,
            pipeline_run_id=run.run_id,
            base_dir=curated_base_dir,
        )
        run.complete_success(
            entity_counts={"employee": employee_counts, "case": case_counts},
            reconciliation=reconciliation,
            curated_output=curated_path,
        )
        manifest_path = persist_pipeline_run(run, base_dir=run_metadata_base_dir)
    except Exception as error:
        run.entity_counts = {"employee": employee_counts, "case": case_counts}
        run.complete_failure(error)
        try:
            persist_pipeline_run(run, base_dir=run_metadata_base_dir)
        except Exception:
            logger.exception(
                "Could not persist failure manifest | run_id=%s", run.run_id
            )
        raise

    logger.info(
        "Case operations pipeline succeeded | run_id=%s curated_records=%d",
        run.run_id,
        len(curated_records),
    )
    return CaseOperationsPipelineResult(
        pipeline_run=run,
        curated_records=curated_records,
        curated_path=curated_path,
        manifest_path=manifest_path,
    )

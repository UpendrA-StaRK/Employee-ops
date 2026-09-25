"""Runnable coordinator for the Week 2 case-operations pipeline.

The individual pipeline stages remain independently reusable.  This module is
the deliberately thin command-line composition used for local and container
execution: files -> RAW -> standardization -> schema validation -> quality ->
quarantine -> curated case operations.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.pipelines.case_operations_pipeline import (
    CaseOperationsPipelineResult,
    run_case_operations_pipeline,
)
from app.pipelines.ingestion import ingest_file
from app.pipelines.quality.engine import DataQualityEngine, QualityContext, QualityResult
from app.pipelines.quality.rejection import persist_rejected
from app.pipelines.quality.rules import (
    AllowedEnumRule,
    EmailFormatRule,
    EmployeeReferenceRule,
    RequiredBusinessValueRule,
    UniqueEmployeeIdRule,
)
from app.pipelines.raw import create_run_id, persist_raw, wrap_records
from app.pipelines.run_metadata import PipelineRun
from app.pipelines.schemas.validator import validate_case, validate_employee
from app.pipelines.standardize import (
    StandardizedCase,
    StandardizedEmployee,
    standardize_case,
    standardize_employee,
)


EMPLOYEE_STATUSES = {"ACTIVE", "INACTIVE"}
CASE_STATUSES = {"OPEN", "IN_PROGRESS", "PENDING", "RESOLVED", "CLOSED"}
CASE_CATEGORIES = {"LEAVE", "PAYROLL", "BENEFITS", "ACCESS", "GENERAL"}
CASE_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}


@dataclass(frozen=True)
class FullPipelineResult:
    """Result plus locations for all durable evidence produced by one run."""

    curated: CaseOperationsPipelineResult
    employee_raw_path: Path
    case_raw_path: Path
    employee_rejections_path: Path | None
    case_rejections_path: Path | None


def _source_type(path: Path) -> str:
    return path.suffix.removeprefix(".").lower()


def _validate_employees(records: list[StandardizedEmployee]) -> None:
    for record in records:
        validate_employee(record)


def _validate_cases(records: list[StandardizedCase]) -> None:
    for record in records:
        validate_case(record)


def _employee_quality(records: list[StandardizedEmployee]) -> QualityResult[StandardizedEmployee]:
    return DataQualityEngine(
        [
            RequiredBusinessValueRule("department"),
            RequiredBusinessValueRule("status"),
            AllowedEnumRule("status", EMPLOYEE_STATUSES),
            EmailFormatRule(),
            UniqueEmployeeIdRule(),
        ]
    ).evaluate_batch(records, QualityContext(), "Employee")


def _case_quality(
    records: list[StandardizedCase], *, known_employee_ids: set[str]
) -> QualityResult[StandardizedCase]:
    return DataQualityEngine(
        [
            RequiredBusinessValueRule("category"),
            RequiredBusinessValueRule("status"),
            RequiredBusinessValueRule("priority"),
            AllowedEnumRule("category", CASE_CATEGORIES),
            AllowedEnumRule("status", CASE_STATUSES),
            AllowedEnumRule("priority", CASE_PRIORITIES),
            EmployeeReferenceRule(),
        ]
    ).evaluate_batch(
        records,
        QualityContext(known_employee_ids=known_employee_ids),
        "Case",
    )


def run_from_files(
    *,
    employees_path: Path,
    cases_path: Path,
    output_root: Path = Path("data"),
    run_id: str | None = None,
) -> FullPipelineResult:
    """Execute the existing Week 2 stages from employee and case source files.

    Schema/structural errors intentionally raise, as defined by the existing
    contract boundary.  Business-quality failures are instead persisted in
    quarantine and excluded from curated output.
    """
    current_run_id = run_id or create_run_id()
    employee_input = ingest_file(employees_path)
    case_input = ingest_file(cases_path)

    employee_raw = wrap_records(
        employee_input,
        run_id=current_run_id,
        source_system="employees_file",
        source_type=_source_type(employees_path),
        source_location=str(employees_path),
    )
    case_raw = wrap_records(
        case_input,
        run_id=current_run_id,
        source_system="cases_file",
        source_type=_source_type(cases_path),
        source_location=str(cases_path),
    )
    employee_raw_path = persist_raw(employee_raw, base_dir=output_root / "raw")
    case_raw_path = persist_raw(case_raw, base_dir=output_root / "raw")

    standardized_employees = [standardize_employee(record) for record in employee_raw]
    standardized_cases = [standardize_case(record) for record in case_raw]
    _validate_employees(standardized_employees)
    _validate_cases(standardized_cases)

    employee_quality = _employee_quality(standardized_employees)
    case_quality = _case_quality(
        standardized_cases,
        known_employee_ids={
            record.employee_id
            for record in employee_quality.valid_records
            if record.employee_id is not None
        },
    )
    employee_rejections_path = (
        persist_rejected(employee_quality.rejected_records, base_dir=output_root / "quarantine")
        if employee_quality.rejected_records
        else None
    )
    case_rejections_path = (
        persist_rejected(case_quality.rejected_records, base_dir=output_root / "quarantine")
        if case_quality.rejected_records
        else None
    )

    curated = run_case_operations_pipeline(
        employee_quality=employee_quality,
        case_quality=case_quality,
        pipeline_run=PipelineRun(
            pipeline_name="case_operations",
            run_id=current_run_id,
            source_info={"employees": str(employees_path), "cases": str(cases_path)},
        ),
        curated_base_dir=output_root / "curated",
        run_metadata_base_dir=output_root / "pipeline_runs",
    )
    return FullPipelineResult(
        curated=curated,
        employee_raw_path=employee_raw_path,
        case_raw_path=case_raw_path,
        employee_rejections_path=employee_rejections_path,
        case_rejections_path=case_rejections_path,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Week 2 case-operations pipeline.")
    parser.add_argument("--employees", type=Path, required=True, help="Employee CSV, JSON, or Parquet source.")
    parser.add_argument("--cases", type=Path, required=True, help="Case CSV, JSON, or Parquet source.")
    parser.add_argument("--output-root", type=Path, default=Path("data"), help="Directory for RAW, quarantine, curated, and run outputs.")
    parser.add_argument("--run-id", help="Stable run ID for an intentional idempotent re-run.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_from_files(
        employees_path=args.employees,
        cases_path=args.cases,
        output_root=args.output_root,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "run_id": result.curated.pipeline_run.run_id,
                "curated_output": str(result.curated.curated_path),
                "manifest": str(result.curated.manifest_path),
                "curated_records": len(result.curated.curated_records),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

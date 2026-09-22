"""Curated case-operations dataset for the Employee Operations pipeline.

This module deliberately consumes only records that have already passed Data
Quality.  It does not ingest, standardize, validate, or reject records.

Dataset: ``case_operations``
Grain: one row per valid case.
Join: valid cases LEFT JOIN valid employees on ``employee_id``.

The left join preserves a case when an employee enrichment record is absent.
That condition is explicit in ``employee_matched`` rather than silently
discarding the case.  Duplicate business keys are a pipeline failure: they
would make the intended one-row-per-case grain ambiguous, so this module never
uses ``DISTINCT`` to hide them.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from app.pipelines.serialization import json_default
from app.pipelines.standardize import StandardizedCase, StandardizedEmployee

logger = logging.getLogger(__name__)

_DEFAULT_CURATED_DIR = Path(__file__).parent.parent.parent / "data" / "curated"


class CuratedDataError(Exception):
    """Raised when valid inputs cannot safely produce the declared dataset grain."""


@dataclass(frozen=True)
class CuratedCaseOperation:
    """One case-operation row, at the explicit grain of one row per case.

    ``pipeline_run_id`` links this curated output to its run manifest.
    Employee fields are ``None`` and ``employee_matched`` is false when a
    valid case has no matching valid employee enrichment record.
    """

    pipeline_run_id: str
    case_id: str
    employee_id: str
    category: str | None
    subject: str | None
    description: str | None
    case_status: str | None
    priority: str | None
    case_created_at: datetime | None
    case_updated_at: datetime | None
    employee_matched: bool
    employee_name: str | None
    employee_email: str | None
    employee_department: str | None
    employee_job_title: str | None
    employee_status: str | None
    case_source_system: str
    employee_source_system: str | None


def _index_employees(
    employees: list[StandardizedEmployee],
) -> dict[str, StandardizedEmployee]:
    """Build a one-to-one employee lookup, rejecting duplicate business keys."""
    by_employee_id: dict[str, StandardizedEmployee] = {}
    for employee in employees:
        if employee.employee_id is None:
            raise CuratedDataError("Valid employee record has no employee_id.")
        if employee.employee_id in by_employee_id:
            raise CuratedDataError(
                "Cannot curate case operations: duplicate employee_id "
                f"{employee.employee_id!r} would create an ambiguous join."
            )
        by_employee_id[employee.employee_id] = employee
    return by_employee_id


def build_case_operations(
    valid_cases: list[StandardizedCase],
    valid_employees: list[StandardizedEmployee],
    *,
    pipeline_run_id: str,
) -> list[CuratedCaseOperation]:
    """Create the ``case_operations`` curated dataset.

    Join design:
      - left entity: valid cases
      - right entity: valid employees
      - business key: ``case.employee_id == employee.employee_id``
      - cardinality: many cases to one employee
      - join type: left join
      - unmatched behaviour: retain the case with null employee enrichment
      - output grain: exactly one row per valid case

    Raises:
        CuratedDataError: If either input has a duplicate business key or a
            case lacks its required identifier.  These are pipeline-level
            failures because they make the declared output grain unreliable.
    """
    employees_by_id = _index_employees(valid_employees)
    seen_case_ids: set[str] = set()
    curated_rows: list[CuratedCaseOperation] = []

    for case in valid_cases:
        if case.case_id is None:
            raise CuratedDataError("Valid case record has no case_id.")
        if case.employee_id is None:
            raise CuratedDataError(
                f"Valid case {case.case_id!r} has no employee_id for the curated join."
            )
        if case.case_id in seen_case_ids:
            raise CuratedDataError(
                "Cannot curate case operations: duplicate case_id "
                f"{case.case_id!r} violates the one-row-per-case grain."
            )
        seen_case_ids.add(case.case_id)

        employee = employees_by_id.get(case.employee_id)
        curated_rows.append(
            CuratedCaseOperation(
                pipeline_run_id=pipeline_run_id,
                case_id=case.case_id,
                employee_id=case.employee_id,
                category=case.category,
                subject=case.subject,
                description=case.description,
                case_status=case.status,
                priority=case.priority,
                case_created_at=case.created_at,
                case_updated_at=case.updated_at,
                employee_matched=employee is not None,
                employee_name=employee.name if employee else None,
                employee_email=employee.email if employee else None,
                employee_department=employee.department if employee else None,
                employee_job_title=employee.job_title if employee else None,
                employee_status=employee.status if employee else None,
                case_source_system=case._raw_source_system,
                employee_source_system=(employee._raw_source_system if employee else None),
            )
        )

    logger.info(
        "Curated case operations built | run_id=%s cases=%d employees=%d unmatched=%d",
        pipeline_run_id,
        len(curated_rows),
        len(valid_employees),
        sum(not row.employee_matched for row in curated_rows),
    )
    return curated_rows


def persist_case_operations(
    records: list[CuratedCaseOperation],
    *,
    pipeline_run_id: str,
    base_dir: Path | None = None,
) -> Path:
    """Persist the curated dataset as ``<base_dir>/<run_id>/case_operations.json``.

    An empty list is intentionally persisted for a successful run with no valid
    cases.  It is still useful audit evidence and preserves the declared grain.
    """
    root = base_dir or _DEFAULT_CURATED_DIR
    output_dir = root / pipeline_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "case_operations.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump([asdict(record) for record in records], file, indent=2, default=json_default)

    logger.info(
        "Curated case operations persisted | run_id=%s path=%s records=%d",
        pipeline_run_id,
        output_path,
        len(records),
    )
    return output_path

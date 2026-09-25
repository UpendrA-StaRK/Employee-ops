"""System tests for the actual Week 2 Python pipeline composition."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pipelines.run_case_operations import run_from_files
from app.pipelines.schemas.validator import SchemaValidationError


RUN_ID = "pipeline-test-run"


def test_pipeline_routes_bad_records_and_persists_reconciled_curated_data(
    pipeline_sources: tuple[Path, Path], tmp_path: Path
) -> None:
    employees_path, cases_path = pipeline_sources
    result = run_from_files(
        employees_path=employees_path,
        cases_path=cases_path,
        output_root=tmp_path / "output",
        run_id=RUN_ID,
    )

    assert result.employee_raw_path.exists()
    assert result.case_raw_path.exists()
    assert [record.case_id for record in result.curated.curated_records] == ["c-001", "c-002"]
    assert all(record.employee_id == "e-001" for record in result.curated.curated_records)
    assert all(record.employee_matched for record in result.curated.curated_records)

    employee_rejections = json.loads(result.employee_rejections_path.read_text(encoding="utf-8"))
    case_rejections = json.loads(result.case_rejections_path.read_text(encoding="utf-8"))
    assert len(employee_rejections) == 2
    assert {item["rejection_reasons"][0]["rule_name"] for item in employee_rejections} == {
        "UniqueEmployeeIdRule",
        "AllowedEnumRule_status",
    }
    assert len(case_rejections) == 2
    assert {item["rejection_reasons"][0]["rule_name"] for item in case_rejections} == {
        "EmployeeReferenceRule"
    }

    manifest = json.loads(result.curated.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "SUCCESS"
    assert manifest["entity_counts"]["employee"]["schema_valid_count"] == 4
    assert manifest["entity_counts"]["employee"]["valid_count"] == 2
    assert manifest["entity_counts"]["case"]["rejected_count"] == 2
    assert manifest["entity_counts"]["case"]["curated_count"] == 2


def test_intentional_same_run_id_replaces_curated_output_without_duplicates(
    pipeline_sources: tuple[Path, Path], tmp_path: Path
) -> None:
    employees_path, cases_path = pipeline_sources
    output_root = tmp_path / "output"
    first = run_from_files(employees_path=employees_path, cases_path=cases_path, output_root=output_root, run_id=RUN_ID)
    first_output = first.curated.curated_path.read_text(encoding="utf-8")
    second = run_from_files(employees_path=employees_path, cases_path=cases_path, output_root=output_root, run_id=RUN_ID)

    assert second.curated.curated_path.read_text(encoding="utf-8") == first_output
    persisted = json.loads(second.curated.curated_path.read_text(encoding="utf-8"))
    assert [record["case_id"] for record in persisted] == ["c-001", "c-002"]
    assert len(persisted) == 2


def test_schema_contract_failure_stops_before_quality_routing(tmp_path: Path) -> None:
    employee_path = tmp_path / "employees.json"
    case_path = tmp_path / "cases.json"
    employee_path.write_text("[{\"name\": \"Missing identifier\"}]", encoding="utf-8")
    case_path.write_text("[{\"case_id\": \"c-001\", \"employee_id\": \"e-001\"}]", encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="employee.v1"):
        run_from_files(
            employees_path=employee_path,
            cases_path=case_path,
            output_root=tmp_path / "output",
            run_id=RUN_ID,
        )

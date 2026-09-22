"""Focused tests for Week 2 Parts 7+8 curated data and run metadata."""
from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.pipelines.case_operations_pipeline import (
    _counts_from_quality_result,
    run_case_operations_pipeline,
)
from app.pipelines.curated import (
    CuratedDataError,
    build_case_operations,
    persist_case_operations,
)
from app.pipelines.quality.engine import QualityResult, RuleFailure
from app.pipelines.quality.rejection import RejectedRecord
from app.pipelines.reconciliation import (
    ReconciliationError,
    StageCounts,
    reconcile_case_operations,
    reconcile_quality_counts,
)
from app.pipelines.run_metadata import (
    PipelineRun,
    PipelineRunStatus,
    persist_pipeline_run,
)
from app.pipelines.standardize import StandardizedCase, StandardizedEmployee

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
RUN_ID = "run-parts-7-8"


def _employee(employee_id: str = "employee-1") -> StandardizedEmployee:
    return StandardizedEmployee(
        employee_id=employee_id,
        name="Asha Patel",
        email="asha.patel@example.test",
        department="People Operations",
        job_title="HR Specialist",
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
        _raw_run_id=RUN_ID,
        _raw_source_system="employees_csv",
    )


def _case(case_id: str = "case-1", employee_id: str = "employee-1") -> StandardizedCase:
    return StandardizedCase(
        case_id=case_id,
        employee_id=employee_id,
        category="LEAVE",
        subject="Leave balance query",
        description="Please confirm my remaining leave balance.",
        status="OPEN",
        priority="MEDIUM",
        created_at=NOW,
        updated_at=NOW,
        _raw_run_id=RUN_ID,
        _raw_source_system="cases_json",
    )


def _rejected(entity: str) -> RejectedRecord:
    return RejectedRecord(
        entity=entity,
        run_id=RUN_ID,
        source_system="test_source",
        rejection_reasons=[RuleFailure("Rule", "Validity", "field", "message")],
        record_payload={"id": "rejected"},
        rejected_at="2026-09-22T12:00:00+00:00",
    )


class TestCaseOperationsJoin:
    def test_many_cases_join_to_one_employee_without_multiplication(self):
        rows = build_case_operations(
            [_case("case-1"), _case("case-2")], [_employee()], pipeline_run_id=RUN_ID
        )

        assert [row.case_id for row in rows] == ["case-1", "case-2"]
        assert all(row.employee_name == "Asha Patel" for row in rows)
        assert all(row.employee_matched for row in rows)

    def test_join_uses_employee_id_and_selects_business_fields(self):
        row = build_case_operations([_case()], [_employee()], pipeline_run_id=RUN_ID)[0]

        assert row.employee_id == "employee-1"
        assert row.employee_department == "People Operations"
        assert row.case_status == "OPEN"
        assert row.case_source_system == "cases_json"
        assert row.employee_source_system == "employees_csv"

    def test_unmatched_employee_is_preserved_as_left_join_row(self):
        row = build_case_operations(
            [_case(employee_id="missing-employee")], [], pipeline_run_id=RUN_ID
        )[0]

        assert row.case_id == "case-1"
        assert row.employee_matched is False
        assert row.employee_name is None

    def test_duplicate_employee_key_is_a_pipeline_failure(self):
        with pytest.raises(CuratedDataError, match="duplicate employee_id"):
            build_case_operations(
                [_case()], [_employee(), _employee()], pipeline_run_id=RUN_ID
            )

    def test_duplicate_case_key_is_a_pipeline_failure(self):
        with pytest.raises(CuratedDataError, match="duplicate case_id"):
            build_case_operations(
                [_case(), _case()], [_employee()], pipeline_run_id=RUN_ID
            )

    def test_curated_records_persist_under_the_run_directory(self, tmp_path):
        rows = build_case_operations([_case()], [_employee()], pipeline_run_id=RUN_ID)
        output_path = persist_case_operations(
            rows, pipeline_run_id=RUN_ID, base_dir=tmp_path
        )

        assert output_path == tmp_path / RUN_ID / "case_operations.json"
        persisted = json.loads(output_path.read_text(encoding="utf-8"))
        assert persisted[0]["pipeline_run_id"] == RUN_ID
        assert persisted[0]["case_created_at"] == NOW.isoformat()

    def test_empty_curated_output_is_persisted_as_audit_evidence(self, tmp_path):
        output_path = persist_case_operations(
            [], pipeline_run_id=RUN_ID, base_dir=tmp_path
        )

        assert output_path == tmp_path / RUN_ID / "case_operations.json"
        assert json.loads(output_path.read_text(encoding="utf-8")) == []


class TestReconciliation:
    def test_quality_count_invariant_is_recorded(self):
        counts = StageCounts(3, 3, 3, 1, 2)
        result = reconcile_quality_counts(entity="employee", counts=counts)

        assert result.counts.valid_count == 2
        assert result.invariants_checked == (
            "schema_valid_count == valid_count + rejected_count",
        )

    def test_quality_count_invariant_failure_is_visible(self):
        with pytest.raises(ReconciliationError, match="must equal"):
            reconcile_quality_counts(
                entity="employee", counts=StageCounts(3, 3, 3, 1, 1)
            )

    def test_quality_reconciliation_allows_legitimate_stage_count_changes(self):
        counts = StageCounts(5, 4, 4, 1, 3)

        result = reconcile_quality_counts(entity="employee", counts=counts)

        assert result.counts.input_count == 5
        assert result.counts.standardized_count == 4

    def test_stage_counts_are_immutable(self):
        counts = StageCounts(2, 2, 2, 0, 2)

        with pytest.raises(FrozenInstanceError):
            counts.curated_count = 2  # type: ignore[misc]

    def test_counts_factory_represents_the_current_quality_boundary(self):
        result = QualityResult([_case()], [_rejected("Case")])

        counts = _counts_from_quality_result(result)

        assert counts == StageCounts(2, 2, 2, 1, 1)

    def test_case_grain_invariant_requires_one_curated_row_per_valid_case(self):
        with pytest.raises(ReconciliationError, match="one row per case"):
            reconcile_case_operations(StageCounts(2, 2, 2, 0, 2, curated_count=1))


class TestPipelineRunMetadata:
    def test_successful_run_records_metadata_counts_and_output(self, tmp_path):
        employee_quality = QualityResult([_employee()], [])
        case_quality = QualityResult([_case()], [_rejected("Case")])
        run = PipelineRun(
            pipeline_name="case_operations_curated",
            run_id=RUN_ID,
            started_at=NOW,
            source_info={"employees": "employees.csv", "cases": "cases.json"},
        )

        result = run_case_operations_pipeline(
            employee_quality=employee_quality,
            case_quality=case_quality,
            pipeline_run=run,
            curated_base_dir=tmp_path / "curated",
            run_metadata_base_dir=tmp_path / "runs",
        )

        assert result.pipeline_run.status is PipelineRunStatus.SUCCESS
        assert result.pipeline_run.started_at == NOW
        assert result.pipeline_run.ended_at is not None
        assert result.pipeline_run.entity_counts["case"].rejected_count == 1
        assert result.pipeline_run.entity_counts["case"].curated_count == 1
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["run_id"] == RUN_ID
        assert manifest["status"] == "SUCCESS"
        assert manifest["curated_output"] == str(result.curated_path)
        assert len(manifest["reconciliation"]) == 2

    def test_failed_pipeline_is_marked_failure_and_reraises(self, tmp_path):
        run = PipelineRun(
            pipeline_name="case_operations_curated", run_id=RUN_ID, started_at=NOW
        )

        with pytest.raises(CuratedDataError, match="duplicate case_id"):
            run_case_operations_pipeline(
                employee_quality=QualityResult([_employee()], []),
                case_quality=QualityResult([_case(), _case()], []),
                pipeline_run=run,
                curated_base_dir=tmp_path / "curated",
                run_metadata_base_dir=tmp_path / "runs",
            )

        manifest = json.loads((tmp_path / "runs" / f"{RUN_ID}.json").read_text())
        assert manifest["status"] == "FAILURE"
        assert manifest["ended_at"] is not None
        assert "duplicate case_id" in manifest["error_message"]

    def test_new_pipeline_run_generates_a_unique_identifier(self):
        first = PipelineRun(pipeline_name="case_operations_curated")
        second = PipelineRun(pipeline_name="case_operations_curated")

        assert first.run_id != second.run_id
        assert first.status is PipelineRunStatus.RUNNING

    def test_running_manifest_can_be_persisted_before_processing(self, tmp_path):
        run = PipelineRun(
            pipeline_name="case_operations_curated", run_id=RUN_ID, started_at=NOW
        )
        path = persist_pipeline_run(run, base_dir=tmp_path)

        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted["status"] == "RUNNING"
        assert persisted["ended_at"] is None

    def test_source_info_cannot_silently_override_a_supplied_run(self, tmp_path):
        run = PipelineRun(
            pipeline_name="case_operations_curated", run_id=RUN_ID, started_at=NOW
        )

        with pytest.raises(ValueError, match="cannot override"):
            run_case_operations_pipeline(
                employee_quality=QualityResult([_employee()], []),
                case_quality=QualityResult([_case()], []),
                pipeline_run=run,
                source_info={"cases": "different-source.json"},
                curated_base_dir=tmp_path / "curated",
                run_metadata_base_dir=tmp_path / "runs",
            )

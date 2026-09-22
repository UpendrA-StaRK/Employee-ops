"""Unit tests for the Standardization layer (app/pipelines/standardize.py).

Tests verify:
  1. Representative records standardize correctly.
  2. Field names are normalized as expected.
  3. Type conversions work (strings → datetime).
  4. Whitespace and null normalization behave correctly.
  5. Equivalent records from different source formats produce the same output.
  6. Invalid structural inputs raise StandardizationError.
  7. Unparseable dates become None (not an exception) — business validity deferred.
  8. RAW layer values are preserved before standardization.
"""
from datetime import datetime, timezone

import pytest

from app.pipelines.raw import RawRecord, create_run_id, wrap_records
from app.pipelines.standardize import (
    StandardizationError,
    StandardizedCase,
    StandardizedCaseHistory,
    StandardizedDepartmentReference,
    StandardizedEmployee,
    standardize_case,
    standardize_case_histories,
    standardize_case_history,
    standardize_cases,
    standardize_department_reference,
    standardize_department_references,
    standardize_employee,
    standardize_employees,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_raw(payload: dict, source_system: str = "test_source") -> RawRecord:
    run_id = create_run_id()
    return wrap_records(
        [payload],
        run_id=run_id,
        source_system=source_system,
        source_type="csv",
    )[0]


# ── Employee standardization ──────────────────────────────────────────────────

class TestStandardizeEmployee:
    CLEAN_EMPLOYEE = {
        "employee_id": "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9",
        "name": "James Verma",
        "email": "james.verma@corp.example.com",
        "department": "Human Resources",
        "job_title": "HR Coordinator",
        "status": "INACTIVE",
        "created_at": "2025-03-28T15:03:01+00:00",
        "updated_at": "2025-04-04T09:37:25+00:00",
    }

    def test_returns_standardized_employee(self):
        raw = _make_raw(self.CLEAN_EMPLOYEE)
        result = standardize_employee(raw)
        assert isinstance(result, StandardizedEmployee)

    def test_fields_mapped_correctly(self):
        raw = _make_raw(self.CLEAN_EMPLOYEE)
        result = standardize_employee(raw)
        assert result.employee_id == "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9"
        assert result.name == "James Verma"
        assert result.email == "james.verma@corp.example.com"
        assert result.department == "Human Resources"
        assert result.status == "INACTIVE"

    def test_created_at_is_datetime(self):
        raw = _make_raw(self.CLEAN_EMPLOYEE)
        result = standardize_employee(raw)
        assert isinstance(result.created_at, datetime)
        assert result.created_at.tzinfo is not None  # timezone-aware

    def test_whitespace_stripped(self):
        payload = {**self.CLEAN_EMPLOYEE, "name": "  Alice  ", "status": "ACTIVE "}
        raw = _make_raw(payload)
        result = standardize_employee(raw)
        assert result.name == "Alice"
        assert result.status == "ACTIVE"

    def test_empty_string_becomes_none(self):
        payload = {**self.CLEAN_EMPLOYEE, "name": "", "department": "   "}
        raw = _make_raw(payload)
        result = standardize_employee(raw)
        assert result.name is None
        assert result.department is None

    def test_none_values_become_none(self):
        payload = {**self.CLEAN_EMPLOYEE, "email": None}
        raw = _make_raw(payload)
        result = standardize_employee(raw)
        assert result.email is None

    def test_unparseable_date_becomes_none(self):
        """An invalid date string becomes None — no exception raised here.
        The Data Quality stage decides whether None created_at is an error."""
        payload = {**self.CLEAN_EMPLOYEE, "created_at": "not-a-date"}
        raw = _make_raw(payload)
        result = standardize_employee(raw)
        assert result.created_at is None

    def test_traceability_fields_set(self):
        raw = _make_raw(self.CLEAN_EMPLOYEE, source_system="employees_csv")
        result = standardize_employee(raw)
        assert result._raw_run_id == raw.run_id
        assert result._raw_source_system == "employees_csv"

    def test_csv_and_json_sources_produce_same_result(self):
        """Two records with the same data from different source systems should
        standardize to the same StandardizedEmployee (modulo traceability fields)."""
        raw_csv = _make_raw(self.CLEAN_EMPLOYEE, source_system="employees_csv")
        raw_json = _make_raw(self.CLEAN_EMPLOYEE, source_system="employees_json")
        result_csv = standardize_employee(raw_csv)
        result_json = standardize_employee(raw_json)
        # Business fields must be identical
        assert result_csv.employee_id == result_json.employee_id
        assert result_csv.name == result_json.name
        assert result_csv.status == result_json.status
        assert result_csv.created_at == result_json.created_at

    def test_invalid_payload_raises_standardization_error(self):
        raw = RawRecord(
            run_id=create_run_id(),
            source_system="test",
            source_type="csv",
            ingested_at="2025-01-01T00:00:00+00:00",
            payload="not a dict",  # type: ignore[arg-type]
        )
        with pytest.raises(StandardizationError):
            standardize_employee(raw)

    def test_batch_standardize_employees(self):
        raw = _make_raw(self.CLEAN_EMPLOYEE)
        results = standardize_employees([raw])
        assert len(results) == 1
        assert isinstance(results[0], StandardizedEmployee)


# ── Case standardization ──────────────────────────────────────────────────────

class TestStandardizeCase:
    CLEAN_CASE = {
        "case_id": "3ceddf2d-839f-4c50-9223-b5135496f63c",
        "employee_id": "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9",
        "category": "LEAVE",
        "subject": "Parental leave policy clarification",
        "description": "Querying eligibility.",
        "status": "CLOSED",
        "priority": "MEDIUM",
        "created_at": "2024-10-19T03:37:03+00:00",
        "updated_at": "2024-10-19T19:14:40+00:00",
    }

    def test_returns_standardized_case(self):
        result = standardize_case(_make_raw(self.CLEAN_CASE))
        assert isinstance(result, StandardizedCase)

    def test_fields_correct(self):
        result = standardize_case(_make_raw(self.CLEAN_CASE))
        assert result.case_id == "3ceddf2d-839f-4c50-9223-b5135496f63c"
        assert result.category == "LEAVE"
        assert result.status == "CLOSED"
        assert result.priority == "MEDIUM"

    def test_timestamps_parsed(self):
        result = standardize_case(_make_raw(self.CLEAN_CASE))
        assert isinstance(result.created_at, datetime)

    def test_batch_standardize_cases(self):
        results = standardize_cases([_make_raw(self.CLEAN_CASE)])
        assert len(results) == 1


# ── CaseHistory standardization ───────────────────────────────────────────────

class TestStandardizeCaseHistory:
    CLEAN_HISTORY = {
        "history_id": "d92c9227-eadf-4085-bfcb-75468eb22579",
        "case_id": "3ceddf2d-839f-4c50-9223-b5135496f63c",
        "old_status": None,
        "new_status": "OPEN",
        "comment": "Additional documentation requested.",
        "changed_by": "system",
        "created_at": "2024-10-19T03:37:03+00:00",
    }

    def test_returns_standardized_case_history(self):
        result = standardize_case_history(_make_raw(self.CLEAN_HISTORY))
        assert isinstance(result, StandardizedCaseHistory)

    def test_null_old_status_preserved_as_none(self):
        """old_status=None for the initial history record must remain None."""
        result = standardize_case_history(_make_raw(self.CLEAN_HISTORY))
        assert result.old_status is None

    def test_created_at_parsed(self):
        result = standardize_case_history(_make_raw(self.CLEAN_HISTORY))
        assert isinstance(result.created_at, datetime)

    def test_batch(self):
        results = standardize_case_histories([_make_raw(self.CLEAN_HISTORY)])
        assert len(results) == 1


# ── DepartmentReference standardization ──────────────────────────────────────

class TestStandardizeDepartmentReference:
    DEPT = {"code": "HR", "name": "Human Resources"}

    def test_returns_standardized_department(self):
        result = standardize_department_reference(_make_raw(self.DEPT))
        assert isinstance(result, StandardizedDepartmentReference)

    def test_code_and_name(self):
        result = standardize_department_reference(_make_raw(self.DEPT))
        assert result.code == "HR"
        assert result.name == "Human Resources"

    def test_whitespace_stripped(self):
        result = standardize_department_reference(
            _make_raw({"code": "  HR  ", "name": "  Human Resources  "})
        )
        assert result.code == "HR"
        assert result.name == "Human Resources"

    def test_batch(self):
        depts = [{"code": "HR", "name": "Human Resources"}, {"code": "ENG", "name": "Engineering"}]
        results = standardize_department_references(
            [_make_raw(d) for d in depts]
        )
        assert len(results) == 2

    def test_invalid_payload_raises(self):
        raw = RawRecord(
            run_id=create_run_id(),
            source_system="rest_departments",
            source_type="rest",
            ingested_at="2025-01-01T00:00:00+00:00",
            payload=42,  # type: ignore[arg-type]
        )
        with pytest.raises(StandardizationError):
            standardize_department_reference(raw)


# ── Boundary: RAW does NOT standardize ───────────────────────────────────────

class TestRawDoesNotStandardize:
    """Ensure that after wrap_records, the payload is still the raw original."""

    def test_whitespace_still_in_raw_payload(self):
        from app.pipelines.raw import wrap_records, create_run_id
        records = [{"name": "  Alice  ", "status": "ACTIVE "}]
        raw_list = wrap_records(
            records,
            run_id=create_run_id(),
            source_system="employees_csv",
            source_type="csv",
        )
        # RAW must preserve — no stripping
        assert raw_list[0].payload["name"] == "  Alice  "
        assert raw_list[0].payload["status"] == "ACTIVE "

    def test_invalid_date_still_in_raw_payload(self):
        from app.pipelines.raw import wrap_records, create_run_id
        records = [{"created_at": "not-a-date"}]
        raw_list = wrap_records(
            records,
            run_id=create_run_id(),
            source_system="employees_csv",
            source_type="csv",
        )
        assert raw_list[0].payload["created_at"] == "not-a-date"

    def test_standardization_strips_but_raw_does_not(self):
        from app.pipelines.raw import wrap_records, create_run_id
        records = [{"employee_id": "e1", "name": "  Alice  ", "status": "ACTIVE "}]
        raw_list = wrap_records(
            records,
            run_id=create_run_id(),
            source_system="employees_csv",
            source_type="csv",
        )
        # RAW: unchanged
        assert raw_list[0].payload["name"] == "  Alice  "
        # Standardized: stripped
        result = standardize_employee(raw_list[0])
        assert result.name == "Alice"
        assert result.status == "ACTIVE"

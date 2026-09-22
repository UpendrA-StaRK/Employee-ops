"""Unit tests for the RAW layer (app/pipelines/raw.py).

Tests verify:
  1. Source records reach RAW wrapped in metadata.
  2. Original source values are preserved byte-for-byte.
  3. Source metadata is attached correctly.
  4. Multiple source records can be represented.
  5. Multiple pipeline runs can be distinguished (different run_ids).
  6. RAW does NOT transform values.
  7. Persistence round-trips correctly.
"""
import json
from pathlib import Path

import pytest

from app.pipelines.raw import (
    RawRecord,
    create_run_id,
    load_raw,
    persist_raw,
    wrap_records,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

EMPLOYEE_ROW = {
    "employee_id": "emp-001",
    "name": "  Alice  ",         # leading/trailing whitespace — must be preserved
    "email": "alice@corp.example.com",
    "department": "HR",
    "job_title": "HR Coordinator",
    "status": "ACTIVE ",         # trailing space — must be preserved
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-06-01T00:00:00+00:00",
}

BAD_DATE_ROW = {
    "employee_id": "emp-002",
    "name": "Bob",
    "hire_date": "not-a-date",   # invalid value — RAW must preserve it
    "status": "ZOMBIE",          # invalid business value — RAW must preserve it
}


# ── create_run_id ─────────────────────────────────────────────────────────────

class TestCreateRunId:
    def test_returns_string(self):
        assert isinstance(create_run_id(), str)

    def test_unique_per_call(self):
        assert create_run_id() != create_run_id()

    def test_uuid_format(self):
        import re
        run_id = create_run_id()
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            run_id,
        )


# ── wrap_records ──────────────────────────────────────────────────────────────

class TestWrapRecords:
    def test_returns_raw_records(self):
        run_id = create_run_id()
        results = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        assert len(results) == 1
        assert isinstance(results[0], RawRecord)

    def test_metadata_attached(self):
        run_id = create_run_id()
        results = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
            source_location="data/generated/employees.csv",
        )
        r = results[0]
        assert r.run_id == run_id
        assert r.source_system == "employees_csv"
        assert r.source_type == "csv"
        assert r.source_location == "data/generated/employees.csv"
        assert r.ingested_at  # non-empty ISO timestamp

    def test_payload_is_original_dict(self):
        """Payload must be the exact original dict — not a copy with changes."""
        run_id = create_run_id()
        results = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        # Check every key/value is identical to the source
        assert results[0].payload == EMPLOYEE_ROW

    def test_whitespace_preserved_in_payload(self):
        """RAW must NOT strip whitespace — that is standardization's job."""
        run_id = create_run_id()
        results = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        assert results[0].payload["name"] == "  Alice  "
        assert results[0].payload["status"] == "ACTIVE "

    def test_invalid_values_preserved(self):
        """RAW must NOT reject or modify business-invalid values."""
        run_id = create_run_id()
        results = wrap_records(
            [BAD_DATE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        assert results[0].payload["hire_date"] == "not-a-date"
        assert results[0].payload["status"] == "ZOMBIE"

    def test_multiple_records(self):
        run_id = create_run_id()
        records = [EMPLOYEE_ROW, BAD_DATE_ROW]
        results = wrap_records(
            records,
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        assert len(results) == 2

    def test_empty_input(self):
        results = wrap_records(
            [],
            run_id=create_run_id(),
            source_system="employees_csv",
            source_type="csv",
        )
        assert results == []

    def test_multiple_run_ids_are_distinguishable(self):
        """Records from two runs must carry different run_ids."""
        run_a = create_run_id()
        run_b = create_run_id()
        result_a = wrap_records([EMPLOYEE_ROW], run_id=run_a,
                                source_system="s", source_type="csv")
        result_b = wrap_records([EMPLOYEE_ROW], run_id=run_b,
                                source_system="s", source_type="csv")
        assert result_a[0].run_id != result_b[0].run_id

    def test_null_values_preserved(self):
        """None values in source dicts must be carried through unchanged."""
        row_with_nulls = {"employee_id": "emp-003", "name": None, "status": None}
        run_id = create_run_id()
        results = wrap_records(
            [row_with_nulls],
            run_id=run_id,
            source_system="employees_json",
            source_type="json",
        )
        assert results[0].payload["name"] is None
        assert results[0].payload["status"] is None


# ── persist_raw / load_raw ───────────────────────────────────────────────────

class TestPersistAndLoad:
    def test_persist_creates_file(self, tmp_path: Path):
        run_id = create_run_id()
        records = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        output_path = persist_raw(records, base_dir=tmp_path)
        assert output_path.exists()

    def test_output_path_structure(self, tmp_path: Path):
        run_id = create_run_id()
        records = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        output_path = persist_raw(records, base_dir=tmp_path)
        # Must be: <base_dir>/<run_id>/employees_csv.json
        assert output_path.parent.name == run_id
        assert output_path.name == "employees_csv.json"

    def test_file_is_valid_json(self, tmp_path: Path):
        run_id = create_run_id()
        records = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        output_path = persist_raw(records, base_dir=tmp_path)
        with output_path.open() as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_load_round_trips(self, tmp_path: Path):
        run_id = create_run_id()
        records = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        output_path = persist_raw(records, base_dir=tmp_path)
        loaded = load_raw(output_path)
        assert len(loaded) == 1
        assert loaded[0].run_id == run_id
        assert loaded[0].payload == EMPLOYEE_ROW

    def test_multiple_sources_separate_files(self, tmp_path: Path):
        """Each source_system gets its own file within the same run directory."""
        run_id = create_run_id()
        emp_records = wrap_records(
            [EMPLOYEE_ROW],
            run_id=run_id,
            source_system="employees_csv",
            source_type="csv",
        )
        case_records = wrap_records(
            [{"case_id": "c-001", "status": "OPEN"}],
            run_id=run_id,
            source_system="cases_json",
            source_type="json",
        )
        path_emp = persist_raw(emp_records, base_dir=tmp_path)
        path_cases = persist_raw(case_records, base_dir=tmp_path)
        # Both in same run dir, different filenames
        assert path_emp.parent == path_cases.parent
        assert path_emp.name != path_cases.name

    def test_persist_empty_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="No RAW records"):
            persist_raw([], base_dir=tmp_path)

    def test_load_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_raw(tmp_path / "nonexistent.json")

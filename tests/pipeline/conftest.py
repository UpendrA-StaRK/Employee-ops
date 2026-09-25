"""Deterministic, deliberately mixed source data for pipeline tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def pipeline_sources(tmp_path: Path) -> tuple[Path, Path]:
    """Write small heterogeneous sources with known valid and rejected records."""
    employees = [
        {"employee_id": "e-001", "name": "Asha Patel", "email": "asha@example.test", "department": "People Operations", "job_title": "Specialist", "status": "ACTIVE", "created_at": "2026-09-01T00:00:00+00:00", "updated_at": "2026-09-02T00:00:00+00:00"},
        {"employee_id": "e-002", "name": "Leo Chen", "email": "leo@example.test", "department": "Engineering", "job_title": "Engineer", "status": "ACTIVE", "created_at": "2026-09-01T00:00:00+00:00", "updated_at": "2026-09-03T00:00:00+00:00"},
        {"employee_id": "e-002", "name": "Duplicate Leo", "email": "duplicate@example.test", "department": "Engineering", "job_title": "Engineer", "status": "ACTIVE", "created_at": "2026-09-01T00:00:00+00:00", "updated_at": "2026-09-03T00:00:00+00:00"},
        {"employee_id": "e-003", "name": "Invalid Status", "email": "invalid@example.test", "department": "Finance", "job_title": "Analyst", "status": "UNKNOWN", "created_at": "2026-09-01T00:00:00+00:00", "updated_at": "2026-09-03T00:00:00+00:00"},
    ]
    cases = [
        {"case_id": "c-001", "employee_id": "e-001", "category": "LEAVE", "subject": "Leave balance", "description": "Check leave balance", "status": "OPEN", "priority": "MEDIUM", "created_at": "2026-09-04T00:00:00+00:00", "updated_at": "2026-09-04T00:00:00+00:00"},
        {"case_id": "c-002", "employee_id": "e-001", "category": "ACCESS", "subject": "VPN access", "description": "VPN cannot connect", "status": "IN_PROGRESS", "priority": "HIGH", "created_at": "2026-09-05T00:00:00+00:00", "updated_at": "2026-09-05T00:00:00+00:00"},
        {"case_id": "c-003", "employee_id": "e-003", "category": "PAYROLL", "subject": "Pay", "description": "Missing payment", "status": "OPEN", "priority": "LOW", "created_at": "2026-09-06T00:00:00+00:00", "updated_at": "2026-09-06T00:00:00+00:00"},
        {"case_id": "c-004", "employee_id": "missing", "category": "GENERAL", "subject": "Question", "description": "General question", "status": "OPEN", "priority": "LOW", "created_at": "2026-09-06T00:00:00+00:00", "updated_at": "2026-09-06T00:00:00+00:00"},
    ]
    employee_path = tmp_path / "employees.json"
    case_path = tmp_path / "cases.json"
    employee_path.write_text(json.dumps(employees), encoding="utf-8")
    case_path.write_text(json.dumps(cases), encoding="utf-8")
    return employee_path, case_path

"""Unit tests for Part 6 — Data Quality + Rejected Records.

Tests cover:
  1. Valid records passing.
  2. Completeness (missing required business value).
  3. Validity (invalid domain values, invalid email).
  4. Uniqueness (duplicate employee_ids detected).
  5. Referential Integrity (unknown reference rejected).
  6. Multiple failures on a single record.
  7. Rejection representation (RuleFailure, RejectedRecord).
  8. Separation (valid records don't go to rejected, rejected don't go to valid).
  9. System failures bubbling up.
"""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from app.pipelines.quality import (
    AllowedEnumRule,
    DataQualityEngine,
    EmailFormatRule,
    EmployeeReferenceRule,
    QualityContext,
    QualityRule,
    RejectedRecord,
    RequiredBusinessValueRule,
    RuleFailure,
    UniqueEmployeeIdRule,
    persist_rejected,
)


# ---------------------------------------------------------------------------
# Test Mocks / Fixtures
# ---------------------------------------------------------------------------

class MockStandardizedEmployee:
    """A minimal mock of the standardized employee for testing rules."""
    def __init__(self, employee_id, email, department, status):
        self.employee_id = employee_id
        self.email = email
        self.department = department
        self.status = status
        self._raw_run_id = "run-123"
        self._raw_source_system = "csv-test"

class MockStandardizedCase:
    def __init__(self, case_id, employee_id):
        self.case_id = case_id
        self.employee_id = employee_id
        self._raw_run_id = "run-123"
        self._raw_source_system = "json-test"


@pytest.fixture
def base_context():
    return QualityContext(known_employee_ids={"emp-1", "emp-2"})


@pytest.fixture
def employee_rules():
    return [
        RequiredBusinessValueRule(field_name="department"),
        AllowedEnumRule(field_name="status", allowed_values={"ACTIVE", "INACTIVE"}),
        EmailFormatRule(field_name="email"),
        UniqueEmployeeIdRule(field_name="employee_id"),
    ]


@pytest.fixture
def engine(employee_rules):
    return DataQualityEngine(rules=employee_rules)


# ---------------------------------------------------------------------------
# Rule Tests (Testing Individual Dimensions)
# ---------------------------------------------------------------------------

def test_completeness_rule_passes():
    rule = RequiredBusinessValueRule("department")
    record = MockStandardizedEmployee("e1", "x@y.com", "HR", "ACTIVE")
    failure = rule.evaluate(record, QualityContext())
    assert failure is None


def test_completeness_rule_fails_on_none():
    rule = RequiredBusinessValueRule("department")
    record = MockStandardizedEmployee("e1", "x@y.com", None, "ACTIVE")
    failure = rule.evaluate(record, QualityContext())
    assert failure is not None
    assert failure.dimension == "Completeness"
    assert failure.field == "department"


def test_validity_enum_rule_passes():
    rule = AllowedEnumRule("status", {"ACTIVE", "INACTIVE"})
    record = MockStandardizedEmployee("e1", "x@y.com", "HR", "ACTIVE")
    failure = rule.evaluate(record, QualityContext())
    assert failure is None


def test_validity_enum_rule_fails():
    rule = AllowedEnumRule("status", {"ACTIVE", "INACTIVE"})
    record = MockStandardizedEmployee("e1", "x@y.com", "HR", "ZOMBIE")
    failure = rule.evaluate(record, QualityContext())
    assert failure is not None
    assert "ZOMBIE" in failure.message


def test_validity_email_rule_fails():
    rule = EmailFormatRule("email")
    record = MockStandardizedEmployee("e1", "not-an-email", "HR", "ACTIVE")
    failure = rule.evaluate(record, QualityContext())
    assert failure is not None
    assert failure.field == "email"


def test_uniqueness_rule_detects_duplicate():
    rule = UniqueEmployeeIdRule("employee_id")
    context = QualityContext()
    
    rec1 = MockStandardizedEmployee("e1", "a@b.com", "HR", "ACTIVE")
    rec2 = MockStandardizedEmployee("e1", "c@d.com", "ENG", "ACTIVE")
    
    # First should pass
    assert rule.evaluate(rec1, context) is None
    # Second should fail
    failure = rule.evaluate(rec2, context)
    assert failure is not None
    assert failure.dimension == "Uniqueness"


def test_referential_integrity_rule_fails_unknown(base_context):
    rule = EmployeeReferenceRule("employee_id")
    
    # emp-1 is known
    rec_valid = MockStandardizedCase("c1", "emp-1")
    assert rule.evaluate(rec_valid, base_context) is None
    
    # emp-99 is unknown
    rec_invalid = MockStandardizedCase("c2", "emp-99")
    failure = rule.evaluate(rec_invalid, base_context)
    assert failure is not None
    assert failure.dimension == "Referential Integrity"


# ---------------------------------------------------------------------------
# Engine Tests (Separation, Multiple Failures, System Errors)
# ---------------------------------------------------------------------------

def test_engine_valid_records_separated(engine, base_context):
    # Two valid records
    records = [
        MockStandardizedEmployee("emp-3", "a@b.com", "HR", "ACTIVE"),
        MockStandardizedEmployee("emp-4", "c@d.com", "ENG", "INACTIVE"),
    ]
    result = engine.evaluate_batch(records, base_context, "Employee")
    
    assert len(result.valid_records) == 2
    assert len(result.rejected_records) == 0


def test_engine_rejected_records_separated(engine, base_context):
    # One valid, one invalid
    records = [
        MockStandardizedEmployee("emp-3", "a@b.com", "HR", "ACTIVE"),
        # Invalid: email format, enum status
        MockStandardizedEmployee("emp-4", "bad-email", "ENG", "ZOMBIE"),
    ]
    result = engine.evaluate_batch(records, base_context, "Employee")
    
    assert len(result.valid_records) == 1
    assert len(result.rejected_records) == 1
    assert result.valid_records[0].employee_id == "emp-3"


def test_engine_multiple_failures_collected(engine, base_context):
    # Record has 3 failures: missing department, bad email, bad status
    record = MockStandardizedEmployee("emp-3", "bad-email", None, "ZOMBIE")
    
    result = engine.evaluate_batch([record], base_context, "Employee")
    assert len(result.valid_records) == 0
    assert len(result.rejected_records) == 1
    
    reasons = result.rejected_records[0].rejection_reasons
    assert len(reasons) == 3
    failed_fields = {f.field for f in reasons}
    assert failed_fields == {"department", "status", "email"}


def test_system_failure_bubbles_up(base_context):
    """Test that a pure programming error in a rule fails the whole pipeline."""
    class CrashingRule:
        dimension = "Crash"
        name = "CrashRule"
        def evaluate(self, record, context):
            raise TypeError("System failure injected for testing")
            
    engine = DataQualityEngine(rules=[CrashingRule()])
    
    with pytest.raises(TypeError, match="System failure"):
        engine.evaluate_batch([MockStandardizedEmployee("e", "x@y.com", "HR", "A")], base_context, "Employee")


# ---------------------------------------------------------------------------
# Rejection & Persistence Tests
# ---------------------------------------------------------------------------

def test_rejection_representation(engine, base_context):
    record = MockStandardizedEmployee("emp-3", "bad-email", "HR", "ACTIVE")
    result = engine.evaluate_batch([record], base_context, "Employee")
    
    rejected = result.rejected_records[0]
    assert rejected.entity == "Employee"
    assert rejected.run_id == "run-123"
    assert rejected.source_system == "csv-test"
    assert rejected.rejected_at != ""
    assert isinstance(rejected.record_payload, dict)
    assert rejected.record_payload["employee_id"] == "emp-3"


def test_persist_rejected(tmp_path):
    failures = [RuleFailure("TestRule", "Validity", "field", "message")]
    record = RejectedRecord(
        entity="Employee",
        run_id="run-999",
        source_system="source-X",
        rejection_reasons=failures,
        record_payload={"id": 1},
    )
    
    output_path = persist_rejected([record], base_dir=tmp_path)
    
    assert output_path.exists()
    assert "run-999" in str(output_path)
    
    with output_path.open() as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["entity"] == "Employee"
        assert len(data[0]["rejection_reasons"]) == 1

def test_persist_empty_rejected_raises():
    with pytest.raises(ValueError, match="No rejected records"):
        persist_rejected([])

"""Unit tests for Part 5 — Schemas + Data Contracts.

Tests cover:
  1. Schema structure — fields, types, required/optional, nullable, identifiers,
     schema version constants.
  2. Schema validation — valid records pass; specific failure modes raise
     SchemaValidationError with informative errors.
  3. Schema mismatch — missing required field, wrong type, invalid structure.
  4. Identifier fields — each schema exposes the correct IDENTIFIER_FIELDS.
  5. Data contracts — schema_version reference, producer/consumer, required fields,
     identifier fields, compatibility rules.
  6. Exception boundary — SchemaValidationError is NOT StandardizationError.
  7. Pipeline integration — validate_* is callable after standardize_*.
  8. Compatibility rules — both compatible and breaking changes are documented.

Fixtures use the same deterministic payloads as test_standardize.py.
No random data; no external services; no DB required.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    standardize_case_history,
    standardize_department_reference,
    standardize_employee,
)
from app.pipelines.schemas import (
    CASE_CONTRACT,
    CASE_HISTORY_CONTRACT,
    DEPARTMENT_REFERENCE_CONTRACT,
    EMPLOYEE_CONTRACT,
    CaseHistorySchemaV1,
    CaseSchemaV1,
    DepartmentReferenceSchemaV1,
    EmployeeSchemaV1,
    SchemaValidationError,
    SchemaValidationResult,
    validate_case,
    validate_case_history,
    validate_department_reference,
    validate_employee,
)
from app.pipelines.schemas.contracts import DataContract, CompatibilityRules


# ---------------------------------------------------------------------------
# Helpers — reuse the same _make_raw pattern from test_standardize.py
# ---------------------------------------------------------------------------

def _make_raw(payload: dict, source_system: str = "test_source") -> RawRecord:
    return wrap_records(
        [payload],
        run_id=create_run_id(),
        source_system=source_system,
        source_type="csv",
    )[0]


# Canonical clean payloads (same as test_standardize.py)
_CLEAN_EMPLOYEE = {
    "employee_id": "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9",
    "name": "James Verma",
    "email": "james.verma@corp.example.com",
    "department": "Human Resources",
    "job_title": "HR Coordinator",
    "status": "INACTIVE",
    "created_at": "2025-03-28T15:03:01+00:00",
    "updated_at": "2025-04-04T09:37:25+00:00",
}

_CLEAN_CASE = {
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

_CLEAN_HISTORY = {
    "history_id": "d92c9227-eadf-4085-bfcb-75468eb22579",
    "case_id": "3ceddf2d-839f-4c50-9223-b5135496f63c",
    "old_status": None,
    "new_status": "OPEN",
    "comment": "Additional documentation requested.",
    "changed_by": "system",
    "created_at": "2024-10-19T03:37:03+00:00",
}

_CLEAN_DEPT = {"code": "HR", "name": "Human Resources"}


# Helpers to produce standardized records from clean payloads
def _std_employee(**overrides) -> StandardizedEmployee:
    return standardize_employee(_make_raw({**_CLEAN_EMPLOYEE, **overrides}))

def _std_case(**overrides) -> StandardizedCase:
    return standardize_case(_make_raw({**_CLEAN_CASE, **overrides}))

def _std_history(**overrides) -> StandardizedCaseHistory:
    return standardize_case_history(_make_raw({**_CLEAN_HISTORY, **overrides}))

def _std_dept(**overrides) -> StandardizedDepartmentReference:
    return standardize_department_reference(_make_raw({**_CLEAN_DEPT, **overrides}))


# ===========================================================================
# 1. Schema structure
# ===========================================================================

class TestSchemaVersionConstants:
    """Each schema class must expose a SCHEMA_VERSION ClassVar."""

    def test_employee_schema_version(self):
        assert EmployeeSchemaV1.SCHEMA_VERSION == "employee.v1"

    def test_case_schema_version(self):
        assert CaseSchemaV1.SCHEMA_VERSION == "case.v1"

    def test_case_history_schema_version(self):
        assert CaseHistorySchemaV1.SCHEMA_VERSION == "case_history.v1"

    def test_department_reference_schema_version(self):
        assert DepartmentReferenceSchemaV1.SCHEMA_VERSION == "department_reference.v1"


class TestIdentifierFields:
    """Each schema must declare the correct identifier field(s)."""

    def test_employee_identifier(self):
        assert "employee_id" in EmployeeSchemaV1.IDENTIFIER_FIELDS

    def test_case_identifier(self):
        assert "case_id" in CaseSchemaV1.IDENTIFIER_FIELDS

    def test_case_history_identifier(self):
        assert "history_id" in CaseHistorySchemaV1.IDENTIFIER_FIELDS

    def test_department_reference_identifier(self):
        assert "code" in DepartmentReferenceSchemaV1.IDENTIFIER_FIELDS

    def test_employee_identifier_is_only_identifier(self):
        """employee_id is the sole identifier — no composite key."""
        assert EmployeeSchemaV1.IDENTIFIER_FIELDS == ("employee_id",)

    def test_case_identifier_is_only_identifier(self):
        assert CaseSchemaV1.IDENTIFIER_FIELDS == ("case_id",)

    def test_case_history_identifier_is_only_identifier(self):
        assert CaseHistorySchemaV1.IDENTIFIER_FIELDS == ("history_id",)


class TestSchemaFieldsAcceptValidData:
    """Pydantic schemas must parse valid standardized data without error."""

    def test_employee_valid_record(self):
        emp = EmployeeSchemaV1.model_validate({
            "employee_id": "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9",
            "name": "James Verma",
            "email": "james.verma@corp.example.com",
            "department": "Human Resources",
            "job_title": "HR Coordinator",
            "status": "INACTIVE",
            "created_at": datetime(2025, 3, 28, 15, 3, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 4, 4, 9, 37, 25, tzinfo=timezone.utc),
        })
        assert emp.employee_id == "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9"
        assert emp.name == "James Verma"

    def test_case_valid_record(self):
        c = CaseSchemaV1.model_validate({
            "case_id": "3ceddf2d-839f-4c50-9223-b5135496f63c",
            "employee_id": "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9",
            "category": "LEAVE",
            "subject": "Policy clarification",
            "description": "Eligibility question",
            "status": "OPEN",
            "priority": "MEDIUM",
            "created_at": None,
            "updated_at": None,
        })
        assert c.case_id == "3ceddf2d-839f-4c50-9223-b5135496f63c"

    def test_case_history_valid_record(self):
        h = CaseHistorySchemaV1.model_validate({
            "history_id": "d92c9227-eadf-4085-bfcb-75468eb22579",
            "case_id": "3ceddf2d-839f-4c50-9223-b5135496f63c",
            "old_status": None,        # nullable — initial record
            "new_status": "OPEN",
            "comment": None,
            "changed_by": "system",
            "created_at": None,
        })
        assert h.history_id == "d92c9227-eadf-4085-bfcb-75468eb22579"
        assert h.old_status is None

    def test_department_reference_valid_record(self):
        d = DepartmentReferenceSchemaV1.model_validate({"code": "HR", "name": "Human Resources"})
        assert d.code == "HR"


class TestNullableFields:
    """Nullable fields must accept None without raising ValidationError."""

    def test_employee_nullable_fields_accept_none(self):
        emp = EmployeeSchemaV1.model_validate({
            "employee_id": "e1",
            "name": "Alice",
            "email": "a@b.com",
            "department": None,
            "job_title": None,
            "status": None,
            "created_at": None,
            "updated_at": None,
        })
        assert emp.department is None
        assert emp.created_at is None

    def test_case_nullable_timestamps_accept_none(self):
        c = CaseSchemaV1.model_validate({
            "case_id": "c1",
            "employee_id": "e1",
            "created_at": None,
            "updated_at": None,
        })
        assert c.created_at is None

    def test_case_history_old_status_nullable(self):
        """old_status is nullable by design for the initial case history record."""
        h = CaseHistorySchemaV1.model_validate({
            "history_id": "h1",
            "case_id": "c1",
            "old_status": None,
            "new_status": "OPEN",
        })
        assert h.old_status is None

    def test_case_history_comment_optional(self):
        """comment may be absent entirely from the data dict."""
        h = CaseHistorySchemaV1.model_validate({
            "history_id": "h1",
            "case_id": "c1",
            "new_status": "OPEN",
        })
        assert h.comment is None


# ===========================================================================
# 2. Schema validation — valid records pass
# ===========================================================================

class TestValidateEmployeePasses:
    def test_valid_employee_passes(self):
        result = validate_employee(_std_employee())
        assert result.is_valid is True

    def test_result_carries_schema_version(self):
        result = validate_employee(_std_employee())
        assert result.schema_version == "employee.v1"

    def test_result_carries_entity(self):
        result = validate_employee(_std_employee())
        assert result.entity == "employee"

    def test_result_errors_empty_on_success(self):
        result = validate_employee(_std_employee())
        assert result.errors == []

    def test_nullable_fields_none_still_passes(self):
        """Standardizer turns unparseable dates to None — schema must still pass."""
        emp = _std_employee(created_at="not-a-date", department="")
        result = validate_employee(emp)
        assert result.is_valid is True


class TestValidateCasePasses:
    def test_valid_case_passes(self):
        result = validate_case(_std_case())
        assert result.is_valid is True

    def test_result_schema_version(self):
        result = validate_case(_std_case())
        assert result.schema_version == "case.v1"


class TestValidateCaseHistoryPasses:
    def test_valid_history_passes(self):
        result = validate_case_history(_std_history())
        assert result.is_valid is True

    def test_null_old_status_passes(self):
        hist = _std_history(old_status=None)
        result = validate_case_history(hist)
        assert result.is_valid is True

    def test_result_schema_version(self):
        result = validate_case_history(_std_history())
        assert result.schema_version == "case_history.v1"


class TestValidateDepartmentReferencePasses:
    def test_valid_dept_passes(self):
        result = validate_department_reference(_std_dept())
        assert result.is_valid is True

    def test_result_schema_version(self):
        result = validate_department_reference(_std_dept())
        assert result.schema_version == "department_reference.v1"


# ===========================================================================
# 3. Schema mismatch — validation MUST fail and raise SchemaValidationError
# ===========================================================================

class TestMissingRequiredField:
    """Missing a non-nullable required field must raise SchemaValidationError."""

    def test_employee_missing_employee_id_raises(self):
        emp = _std_employee()
        emp.employee_id = None  # force None onto a non-nullable field
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_employee(emp)
        err = exc_info.value
        assert err.entity == "employee"
        assert err.schema_version == "employee.v1"
        assert len(err.errors) > 0

    def test_employee_missing_name_raises(self):
        emp = _std_employee()
        emp.name = None
        with pytest.raises(SchemaValidationError):
            validate_employee(emp)

    def test_employee_missing_email_raises(self):
        emp = _std_employee()
        emp.email = None
        with pytest.raises(SchemaValidationError):
            validate_employee(emp)

    def test_case_missing_case_id_raises(self):
        case = _std_case()
        case.case_id = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_case(case)
        assert exc_info.value.entity == "case"

    def test_case_missing_employee_id_raises(self):
        case = _std_case()
        case.employee_id = None
        with pytest.raises(SchemaValidationError):
            validate_case(case)

    def test_history_missing_history_id_raises(self):
        hist = _std_history()
        hist.history_id = None
        with pytest.raises(SchemaValidationError):
            validate_case_history(hist)

    def test_history_missing_case_id_raises(self):
        hist = _std_history()
        hist.case_id = None
        with pytest.raises(SchemaValidationError):
            validate_case_history(hist)

    def test_history_missing_new_status_raises(self):
        hist = _std_history()
        hist.new_status = None
        with pytest.raises(SchemaValidationError):
            validate_case_history(hist)

    def test_dept_missing_code_raises(self):
        dept = _std_dept()
        dept.code = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_department_reference(dept)
        assert exc_info.value.entity == "department_reference"

    def test_dept_missing_name_raises(self):
        dept = _std_dept()
        dept.name = None
        with pytest.raises(SchemaValidationError):
            validate_department_reference(dept)


class TestWrongFieldType:
    """Incompatible field types must raise SchemaValidationError."""

    def test_employee_id_integer_raises(self):
        """employee_id must be str; feeding an integer is a type mismatch."""
        emp = _std_employee()
        emp.employee_id = 12345  # type: ignore[assignment]
        with pytest.raises(SchemaValidationError):
            validate_employee(emp)

    def test_case_id_list_raises(self):
        case = _std_case()
        case.case_id = ["not", "a", "string"]  # type: ignore[assignment]
        with pytest.raises(SchemaValidationError):
            validate_case(case)

    def test_history_id_dict_raises(self):
        hist = _std_history()
        hist.history_id = {"bad": "type"}  # type: ignore[assignment]
        with pytest.raises(SchemaValidationError):
            validate_case_history(hist)

    def test_dept_code_integer_raises(self):
        dept = _std_dept()
        dept.code = 42  # type: ignore[assignment]
        with pytest.raises(SchemaValidationError):
            validate_department_reference(dept)


class TestSchemaValidationErrorContents:
    """SchemaValidationError should carry useful diagnostic information."""

    def test_error_has_entity(self):
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_employee(emp)
        assert exc_info.value.entity == "employee"

    def test_error_has_schema_version(self):
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_employee(emp)
        assert exc_info.value.schema_version == "employee.v1"

    def test_error_has_errors_list(self):
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_employee(emp)
        assert isinstance(exc_info.value.errors, list)
        assert len(exc_info.value.errors) >= 1

    def test_error_message_not_empty(self):
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_employee(emp)
        assert str(exc_info.value)  # must be non-empty


# ===========================================================================
# 4. Exception boundary — SchemaValidationError ≠ StandardizationError
# ===========================================================================

class TestExceptionBoundary:
    """Schema failures and standardization failures are distinct exception types.

    This preserves the conceptual boundary:
      StandardizationError  — payload cannot be structurally standardized
      SchemaValidationError — standardized record does not conform to schema
    """

    def test_schema_validation_error_is_not_standardization_error(self):
        assert not issubclass(SchemaValidationError, StandardizationError)

    def test_standardization_error_is_not_schema_validation_error(self):
        assert not issubclass(StandardizationError, SchemaValidationError)

    def test_catching_standardization_error_does_not_catch_schema_error(self):
        """A handler for StandardizationError must not silently swallow schema failures."""
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError):
            try:
                validate_employee(emp)
            except StandardizationError:
                pytest.fail("SchemaValidationError was swallowed by StandardizationError handler")

    def test_schema_validation_error_is_exception(self):
        assert issubclass(SchemaValidationError, Exception)

    def test_schema_validation_result_is_dataclass(self):
        result = validate_employee(_std_employee())
        assert isinstance(result, SchemaValidationResult)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "entity")
        assert hasattr(result, "schema_version")
        assert hasattr(result, "errors")


# ===========================================================================
# 5. Pipeline integration — validate_* usable after standardize_*
# ===========================================================================

class TestPipelineIntegration:
    """The validate_* functions are invocable immediately after standardize_*."""

    def test_employee_pipeline_boundary(self):
        raw = _make_raw(_CLEAN_EMPLOYEE, source_system="employees_csv")
        standardized = standardize_employee(raw)   # standardization step
        result = validate_employee(standardized)   # schema validation step
        assert result.is_valid is True

    def test_case_pipeline_boundary(self):
        raw = _make_raw(_CLEAN_CASE, source_system="cases_json")
        standardized = standardize_case(raw)
        result = validate_case(standardized)
        assert result.is_valid is True

    def test_case_history_pipeline_boundary(self):
        raw = _make_raw(_CLEAN_HISTORY, source_system="case_history_csv")
        standardized = standardize_case_history(raw)
        result = validate_case_history(standardized)
        assert result.is_valid is True

    def test_department_pipeline_boundary(self):
        raw = _make_raw(_CLEAN_DEPT, source_system="rest_departments")
        standardized = standardize_department_reference(raw)
        result = validate_department_reference(standardized)
        assert result.is_valid is True

    def test_traceability_fields_excluded_from_validation(self):
        """Pipeline metadata fields (_raw_run_id, _raw_source_system) must NOT
        cause a schema validation failure — they are excluded from the dict
        passed to Pydantic."""
        emp = _std_employee()
        assert emp._raw_run_id != ""       # traceability field is present on the dataclass
        result = validate_employee(emp)     # but validation must still pass
        assert result.is_valid is True


# ===========================================================================
# 6. Data contract structure
# ===========================================================================

class TestContractMetadata:
    """Each contract must carry the required metadata fields."""

    @pytest.mark.parametrize("contract,expected_entity", [
        (EMPLOYEE_CONTRACT, "Employee"),
        (CASE_CONTRACT, "Case"),
        (CASE_HISTORY_CONTRACT, "CaseHistory"),
        (DEPARTMENT_REFERENCE_CONTRACT, "DepartmentReference"),
    ])
    def test_contract_entity(self, contract: DataContract, expected_entity: str):
        assert contract.entity == expected_entity

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_producer_not_empty(self, contract: DataContract):
        assert contract.producer

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_consumer_not_empty(self, contract: DataContract):
        assert contract.consumer

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_name_not_empty(self, contract: DataContract):
        assert contract.name

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_required_fields_not_empty(self, contract: DataContract):
        assert len(contract.required_fields) > 0

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_field_types_not_empty(self, contract: DataContract):
        assert len(contract.field_types) > 0


class TestContractSchemaVersionReference:
    """Each contract must reference the correct canonical schema version."""

    def test_employee_contract_schema_version(self):
        assert EMPLOYEE_CONTRACT.schema_version == EmployeeSchemaV1.SCHEMA_VERSION
        assert EMPLOYEE_CONTRACT.schema_version == "employee.v1"

    def test_case_contract_schema_version(self):
        assert CASE_CONTRACT.schema_version == CaseSchemaV1.SCHEMA_VERSION
        assert CASE_CONTRACT.schema_version == "case.v1"

    def test_case_history_contract_schema_version(self):
        assert CASE_HISTORY_CONTRACT.schema_version == CaseHistorySchemaV1.SCHEMA_VERSION
        assert CASE_HISTORY_CONTRACT.schema_version == "case_history.v1"

    def test_department_reference_contract_schema_version(self):
        assert DEPARTMENT_REFERENCE_CONTRACT.schema_version == DepartmentReferenceSchemaV1.SCHEMA_VERSION
        assert DEPARTMENT_REFERENCE_CONTRACT.schema_version == "department_reference.v1"


class TestContractIdentifierFields:
    """Contract identifier_fields must match schema IDENTIFIER_FIELDS."""

    def test_employee_contract_identifier(self):
        assert EMPLOYEE_CONTRACT.identifier_fields == EmployeeSchemaV1.IDENTIFIER_FIELDS
        assert "employee_id" in EMPLOYEE_CONTRACT.identifier_fields

    def test_case_contract_identifier(self):
        assert CASE_CONTRACT.identifier_fields == CaseSchemaV1.IDENTIFIER_FIELDS
        assert "case_id" in CASE_CONTRACT.identifier_fields

    def test_case_history_contract_identifier(self):
        assert CASE_HISTORY_CONTRACT.identifier_fields == CaseHistorySchemaV1.IDENTIFIER_FIELDS
        assert "history_id" in CASE_HISTORY_CONTRACT.identifier_fields

    def test_department_reference_contract_identifier(self):
        assert DEPARTMENT_REFERENCE_CONTRACT.identifier_fields == DepartmentReferenceSchemaV1.IDENTIFIER_FIELDS
        assert "code" in DEPARTMENT_REFERENCE_CONTRACT.identifier_fields


class TestContractRequiredFields:
    """Contracts must list the identifier fields within required_fields."""

    def test_employee_contract_has_employee_id_in_required(self):
        assert "employee_id" in EMPLOYEE_CONTRACT.required_fields

    def test_case_contract_has_case_id_in_required(self):
        assert "case_id" in CASE_CONTRACT.required_fields

    def test_case_history_contract_has_history_id_in_required(self):
        assert "history_id" in CASE_HISTORY_CONTRACT.required_fields

    def test_department_reference_contract_has_code_in_required(self):
        assert "code" in DEPARTMENT_REFERENCE_CONTRACT.required_fields


class TestContractIsFrozen:
    """DataContract is a frozen dataclass — contracts must not be mutable."""

    def test_employee_contract_is_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            EMPLOYEE_CONTRACT.name = "Changed"  # type: ignore[misc]

    def test_case_contract_is_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            CASE_CONTRACT.schema_version = "case.v99"  # type: ignore[misc]


# ===========================================================================
# 7. Compatibility rules
# ===========================================================================

class TestCompatibilityRules:
    """Contracts must document compatible and breaking change categories."""

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_has_compatible_changes(self, contract: DataContract):
        assert isinstance(contract.compatibility, CompatibilityRules)
        assert len(contract.compatibility.compatible_changes) > 0

    @pytest.mark.parametrize("contract", [
        EMPLOYEE_CONTRACT,
        CASE_CONTRACT,
        CASE_HISTORY_CONTRACT,
        DEPARTMENT_REFERENCE_CONTRACT,
    ])
    def test_contract_has_breaking_changes(self, contract: DataContract):
        assert len(contract.compatibility.breaking_changes) > 0

    def test_adding_optional_field_listed_as_compatible(self):
        """Adding a new optional/nullable field must be documented as compatible."""
        compatible_text = " ".join(EMPLOYEE_CONTRACT.compatibility.compatible_changes).lower()
        assert "optional" in compatible_text or "nullable" in compatible_text

    def test_removing_required_field_listed_as_breaking(self):
        breaking_text = " ".join(EMPLOYEE_CONTRACT.compatibility.breaking_changes).lower()
        assert "required" in breaking_text or "removing" in breaking_text

    def test_renaming_identifier_listed_as_breaking(self):
        breaking_text = " ".join(EMPLOYEE_CONTRACT.compatibility.breaking_changes).lower()
        assert "identifier" in breaking_text or "rename" in breaking_text or "renaming" in breaking_text

    def test_type_change_listed_as_breaking(self):
        breaking_text = " ".join(EMPLOYEE_CONTRACT.compatibility.breaking_changes).lower()
        assert "type" in breaking_text


# ===========================================================================
# 8. Schema vs Data Quality boundary
# ===========================================================================

class TestSchemaVsDataQualityBoundary:
    """Schema validation checks structure/types only.
    Business-rule failures belong to Part 6 Data Quality.

    These tests document the boundary explicitly:
    - Schema failure: wrong Python type for a field
    - DQ failure: correct type but business-invalid value (NOT tested here)
    """

    def test_invalid_type_is_schema_failure(self):
        """employee_id=42 (int) is a schema failure — wrong type."""
        emp = _std_employee()
        emp.employee_id = 42  # type: ignore[assignment]
        with pytest.raises(SchemaValidationError):
            validate_employee(emp)

    def test_none_identifier_is_schema_failure(self):
        """employee_id=None for a non-nullable identifier is a schema failure."""
        emp = _std_employee()
        emp.employee_id = None
        with pytest.raises(SchemaValidationError):
            validate_employee(emp)

    def test_valid_type_but_unknown_status_is_not_schema_failure(self):
        """status='ZOMBIE' has a valid str type — schema passes.
        Whether 'ZOMBIE' is a valid business status is a DQ concern (Part 6).
        """
        emp = _std_employee(status="ZOMBIE")
        result = validate_employee(emp)
        assert result.is_valid is True  # type is correct; DQ not our concern here

    def test_unparseable_date_leaving_none_is_not_schema_failure(self):
        """When standardizer can't parse a date, it sets None.
        The schema accepts None for datetime fields (nullable).
        Whether None is acceptable for the business is a DQ concern.
        """
        emp = _std_employee(created_at="not-a-date")
        assert emp.created_at is None  # standardizer produced None
        result = validate_employee(emp)
        assert result.is_valid is True  # None is schema-valid for this field

# Schemas and Data Contracts — Architecture Guide

**Pipeline stage:** Week 2 Part 5  
**Location:** `app/pipelines/schemas/`

---

## 1. What Is a Schema?

A **schema** describes the *structure and expected representation* of a standardized entity record.

It answers:
- What fields exist?
- What Python types are they?
- Which fields are required vs optional?
- Which fields are nullable?
- Which field(s) uniquely identify the entity?

Schemas in this project are **Pydantic v2 `BaseModel` subclasses** defined in [`canonical.py`](../app/pipelines/schemas/canonical.py).

### Example — EmployeeSchemaV1 (simplified)

```
employee_id : str          — required, non-nullable, identifier
name        : str          — required, non-nullable
email       : str          — required, non-nullable
department  : str | None   — required, nullable
job_title   : str | None   — required, nullable
status      : str | None   — required, nullable
created_at  : datetime | None  — required, nullable
updated_at  : datetime | None  — required, nullable
```

A **nullable** field means the field exists but its value may be `None`.  
An **optional** field means the field may be entirely absent from the data.

Schemas do **NOT** validate business rules.  
Example: `status = "ZOMBIE"` passes schema validation (it is a string), but may fail Data Quality (Part 6).

---

## 2. What Is a Data Contract?

A **data contract** defines the explicit expectations between a data *producer* (source system) and the *consumer* (the pipeline).

It adds producer/consumer context to a schema reference:
- Which system produces the data?
- Which pipeline stage consumes it?
- Which schema version is expected?
- Which fields must the producer supply?
- What schema evolution rules apply?

Contracts in this project are **frozen Python dataclasses** defined in [`contracts.py`](../app/pipelines/schemas/contracts.py).

---

## 3. How Schemas and Contracts Relate

```
DATA CONTRACT
    references
        ↓
    SCHEMA VERSION
```

The contract does **not** duplicate the full field list from the schema.  
It references the schema version (`schema_version = "employee.v1"`) and adds the producer/consumer context.

| Concern | Owned by |
|---|---|
| Field names, types, nullability | Schema (canonical.py) |
| Required fields declared by source | Contract (contracts.py) |
| Producer/consumer identity | Contract |
| Schema evolution rules | Contract compatibility rules |

---

## 4. Where Schema Validation Occurs

```
SOURCE
  ↓
INGESTION   (app/pipelines/ingestion.py, db_ingestion.py, rest_ingestion.py)
  ↓
RAW         (app/pipelines/raw.py)            ← wrap + persist original records
  ↓
STANDARDIZATION  (app/pipelines/standardize.py)  ← normalize types, strip whitespace
  ↓
SCHEMA VALIDATION  (app/pipelines/schemas/validator.py)  ← validate against canonical schema
  ↓
DATA QUALITY  (Part 6 — not yet implemented)
  ↓
VALID / CURATED
```

Schema validation is applied **after** standardization because standardized data is the representation downstream stages should be able to rely on.

### How to invoke (after standardization)

```python
from app.pipelines.standardize import standardize_employee
from app.pipelines.schemas import validate_employee, SchemaValidationError

standardized = standardize_employee(raw_record)       # existing step
result = validate_employee(standardized)              # new step — Part 5
# result.is_valid is True on success
# raises SchemaValidationError on any hard mismatch
```

---

## 5. Schema Versioning

Schema versions use the format:

```
<entity>.<version>
```

| Entity | Version string |
|---|---|
| Employee | `employee.v1` |
| Case | `case.v1` |
| CaseHistory | `case_history.v1` |
| DepartmentReference | `department_reference.v1` |

The version is a `ClassVar[str]` constant on each schema class:

```python
class EmployeeSchemaV1(BaseModel):
    SCHEMA_VERSION: ClassVar[str] = "employee.v1"
```

This makes the version:
- inspectable at runtime (`EmployeeSchemaV1.SCHEMA_VERSION`)
- carried on validation results (`SchemaValidationResult.schema_version`)
- carried on error metadata (`SchemaValidationError.schema_version`)
- referenced in the data contract (`EMPLOYEE_CONTRACT.schema_version`)

There is intentionally no external registry, no Kafka schema management, no additional infrastructure.

---

## 6. Schema Mismatches

A **schema mismatch** occurs when a standardized record does not conform to its declared canonical schema.

`SchemaValidationError` is raised — it is **not** silently swallowed.

### Examples of schema failures

| Situation | Error type |
|---|---|
| `employee_id` is `None` when schema requires `str` | `SchemaValidationError` |
| `case_id` is a list instead of a string | `SchemaValidationError` |
| `history_id` is missing (None on a non-nullable field) | `SchemaValidationError` |
| `department_reference.code` is an integer | `SchemaValidationError` |

### Examples of Data Quality failures (NOT schema)

| Situation | Correct type? | Correct stage |
|---|---|---|
| `status = "ZOMBIE"` (unknown value) | ✅ str | Part 6 Data Quality |
| `employee_id` is a valid string but not in the DB | ✅ str | Part 6 Data Quality |
| `created_at = None` (was unparseable) | ✅ None is allowed by schema | Part 6 Data Quality |

### SchemaValidationError vs StandardizationError

| Exception | When raised |
|---|---|
| `StandardizationError` | The raw payload cannot be structurally standardized (e.g. payload is not a dict) |
| `SchemaValidationError` | The *standardized* record does not conform to its canonical schema |

These are distinct exception classes. Catching one does **not** catch the other.

---

## 7. Schema Evolution / Compatibility Rules

Each data contract documents explicit compatibility expectations.

### Generally compatible changes

- Adding a new **optional** field with a nullable type
- Adding a new **nullable** field where None is an acceptable initial value

### Potentially breaking changes

- Removing any existing required field
- Renaming an identifier field (`employee_id`, `case_id`, `history_id`, `code`)
- Changing a field's type incompatibly (e.g. `str → int`)
- Making a nullable field non-nullable when producers may omit it
- Changing identifier field semantics

These rules are documented on `CompatibilityRules` within each contract.  
Enforcement is currently manual/documentary — automated compatibility checking belongs to future tooling.

---

## 8. What Is Deferred to Part 6 (Data Quality)

Part 5 covers schema structure and type conformance only.

Part 6 will cover:

| Concern | Part 6 feature |
|---|---|
| `status` must be one of `{OPEN, CLOSED, ...}` | Enum membership validation |
| `employee_id` must correspond to a real employee | Referential integrity |
| `created_at` must not be `None` | Null-rejection rule |
| `hire_date` must be in the past | Business rule |
| Duplicate records | Deduplication |
| Rejected record routing and quarantine | Rejected-record framework |

None of the above belong to this module.

---

## 9. Module Map

```
app/pipelines/schemas/
    __init__.py       — Public API exports
    canonical.py      — Pydantic schema classes (EmployeeSchemaV1, etc.)
    contracts.py      — DataContract frozen dataclasses + module-level contract instances
    validator.py      — validate_* functions + SchemaValidationError + SchemaValidationResult

tests/unit/
    test_schemas.py   — Part 5 unit tests
```

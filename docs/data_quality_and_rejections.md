# Data Quality & Rejected Records (Part 6)

## 1. What Data Quality Means in This Project

In this pipeline, **Schema Validation** (Part 5) ensures that records are structurally correct (e.g., all fields have the correct Python type, required fields exist). 

**Data Quality** (Part 6) ensures that a structurally valid record makes business sense and can be trusted.

### Examples of the boundary:

| Field | Issue | Fails Schema (Part 5) | Fails Data Quality (Part 6) |
|---|---|---|---|
| `employee_id` | Missing / `None` | ✅ Yes | |
| `employee_id` | Is an integer (`42`) | ✅ Yes | |
| `employee_id` | Is duplicate within the file | | ✅ Yes (Uniqueness rule) |
| `status` | `"ZOMBIE"` (Not an allowed enum) | | ✅ Yes (Validity rule) |
| `email` | `"not_an_email"` (Bad format) | | ✅ Yes (Validity rule) |
| `department` | Empty/`None` but business needs it | | ✅ Yes (Completeness rule) |

---

## 2. Implemented Quality Dimensions & Rules

The `app/pipelines/quality/rules.py` module defines the following concrete rules:

1. **Completeness**
   - `RequiredBusinessValueRule`: Ensures a field that is technically allowed to be `None` by the schema is present because the domain strictly requires it for processing.
2. **Validity**
   - `AllowedEnumRule`: Ensures values match expected domain enumerations (e.g., `ACTIVE`, `CLOSED`).
   - `EmailFormatRule`: Simple regex check for valid email syntax.
3. **Uniqueness**
   - `UniqueEmployeeIdRule`: Tracks seen identifiers during batch evaluation to detect and reject duplicates.
4. **Referential Integrity**
   - `EmployeeReferenceRule`: Confirms that foreign keys (e.g. `employee_id` on a Case) point to known entities, by checking against a populated Context object.

---

## 3. Data Flow: Valid vs. Rejected

The `DataQualityEngine` processes a list of structurally valid records.

It returns a `QualityResult` containing two lists:
1. `valid_records`: Records that passed all quality rules. These continue to the downstream curated storage/processing layers.
2. `rejected_records`: Records that failed one or more quality rules.

```
standardized + schema-valid
    ↓
DataQualityEngine
    ├── valid_records    →  (Part 7+)
    └── rejected_records →  Quarantine
```

---

## 4. Rejection Handling & Quarantine Storage

When a record fails, it is explicitly encapsulated in a `RejectedRecord` dataclass (defined in `app/pipelines/quality/rejection.py`).

### What a Rejection Contains:
- `entity`: e.g. `"Employee"`
- `run_id`: Traceable pipeline run ID
- `source_system`: Source system metadata
- `rejection_reasons`: A list of `RuleFailure` objects. A single record **will** accumulate multiple rule failures if applicable (Requirement #16).
- `record_payload`: The original structurally valid record dumped to a dict.

### Quarantine Storage
Rejected records do not proceed into the curated Data Warehouse. Instead, they are output to file-based quarantine storage matching the existing RAW pipeline patterns:
`data/quarantine/{run_id}/{entity}_rejected.json`

This avoids unnecessary new infrastructure (no Kafka or cloud quarantine systems required).

---

## 5. Error Handling: Record vs. System Failures

**Record-Level Quality Failure:**
- Example: `"ZOMBIE"` status, duplicate employee ID.
- Action: That specific record is appended to `rejected_records`.
- Impact: The pipeline continues happily processing other valid records.

**System-Level Pipeline Failure:**
- Example: Database unavailable, pure Python `TypeError` inside a rule due to developer error.
- Action: The Exception bubbles up unhandled from the engine.
- Impact: The entire pipeline execution halts and fails.

We deliberately **do not** wrap the quality engine in a generic `try/except Exception` block. Genuine system errors must crash the pipeline (Requirement #14).

---

## 6. What is intentionally deferred (Part 7+)
- Incrementality / Idempotency
- Curated Data / Data Warehouse loading
- Cross-source Joins / Reconciliation
- Pipeline-wide Audit logs

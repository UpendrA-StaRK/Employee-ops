# Curated Data, Reconciliation, and Pipeline Runs (Parts 7+8)

## Boundary

This layer starts after Part 6.  It consumes only the `valid_records` in each
`QualityResult`; standardization, schema validation, data-quality evaluation,
and quarantine remain upstream concerns.

```
valid standardized records
    -> case_operations curated join
    -> reconciliation
    -> curated output + run manifest
```

## Curated dataset

### `case_operations`

| Design item | Decision |
|---|---|
| Purpose | Give downstream case-operations users a case with employee context in one record. |
| Grain | Exactly one row per valid case. |
| Left entity | Valid `StandardizedCase` records. |
| Right entity | Valid `StandardizedEmployee` records. |
| Join key | `case.employee_id == employee.employee_id`. |
| Cardinality | Many cases to one employee. |
| Join type | Left join. |
| Unmatched behaviour | Retain the case; set employee enrichment fields to `null` and `employee_matched` to `false`. |
| Selected fields | Case identity, category, subject, description, status, priority, timestamps; employee identity, name, email, department, job title, status; source and pipeline-run metadata. |
| Output | `data/curated/{run_id}/case_operations.json`. |

An employee may have many cases, which is compatible with the one-row-per-case
grain.  Duplicate `employee_id` records would make a case match multiple
employees, and duplicate `case_id` values violate the grain directly.  Both are
raised as `CuratedDataError`; the implementation does not use `DISTINCT` to
mask either situation.

`CaseHistory` is intentionally not joined into this dataset: one case can have
many history events, so doing so would change its grain.  A case-history
curated dataset can be designed separately when there is a downstream need.
`DepartmentReference` is also not joined: employees already carry their
department as a descriptive field, while the current model has no stable
employee-to-department-code relationship.

## Reconciliation

Each run captures these counts for employees and cases:

- input
- standardized
- schema-valid
- rejected
- valid
- curated

The current upstream contract fails the run on standardization or hard schema
errors, so records that reach Data Quality are both standardized and
schema-valid.  The coordinator records that count for the current boundary;
future orchestration can supply distinct counts where a legitimate
transformation changes them.

The enforced invariants are:

```
schema_valid_count == valid_count + rejected_count
case_operations.curated_count == case.valid_count
```

The first verifies quality routing.  The second verifies the declared
one-row-per-valid-case output grain.  A failed invariant raises
`ReconciliationError`, fails the pipeline run, and is not treated as a
record-level rejection.

## Audit/run metadata

`PipelineRun` is the lightweight run manifest.  It records:

- UUID run ID and pipeline name
- start and end timestamps (UTC ISO-8601)
- `RUNNING`, `SUCCESS`, or `FAILURE` status
- source information supplied when a new run is constructed
- per-entity stage counts and reconciliation results
- curated output path
- failure message, where relevant

Run manifests live at `data/pipeline_runs/{run_id}.json`.  A `RUNNING`
manifest is persisted before curated processing.  A run becomes `SUCCESS` only
after reconciliation and curated-data persistence succeed.  On a pipeline
failure, the manifest is updated to `FAILURE` and the original exception is
re-raised.

Use the same run ID when wrapping RAW records and constructing `PipelineRun`
to retain run-level lineage.  Every curated row also contains
`pipeline_run_id`.  A caller that supplies an existing `PipelineRun` must set
its `source_info` at construction; a second `source_info` argument is rejected
rather than silently overwriting caller-owned metadata.

## Deliberate Part 9 boundary

This implementation records what happened in a run.  It does **not** add
watermarks, checkpoints, change-data capture, replay state, idempotency keys,
incremental selection, or retry/replay behaviour.  Those belong to Part 9.

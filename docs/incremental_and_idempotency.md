# Incremental + Idempotent Processing (Part 9)

## 1. What Incremental Processing Means in This Project

In a **full load**, every record from every source is ingested and processed on every run.

In an **incremental load**, only records that have changed since the last successful run are processed.

This project uses a **batch-oriented high-water-mark** strategy.  On each run:

1. Read the committed watermark from the database.
2. Select only records newer than the watermark.
3. Process those records through the full pipeline (Standardize → Schema → DQ → Curated).
4. If processing succeeds: commit the new watermark.
5. If processing fails: leave the watermark unchanged so the next run retries correctly.

---

## 2. Change Indicator (Watermark Field)

| Entity | Change field | Rationale |
|---|---|---|
| `Employee` | `updated_at` | Set at creation; updated on every change |
| `Case` | `updated_at` | Same semantics |
| `CaseHistory` | `created_at` | Append-only table — rows are never updated, only created |

These fields exist in both the synthetic generator output and the standardized dataclasses.  No new field was introduced.

---

## 3. Watermark Boundary Semantics

A **composite watermark** `(watermark_ts, watermark_id)` is used to handle the case where multiple records share the same `updated_at` value.

### Selection rule

A record is **included** in the next incremental batch if:

```
record.updated_at > watermark_ts
OR
(record.updated_at == watermark_ts AND record.entity_id > watermark_id)
```

A record is **excluded** if:

```
record.updated_at < watermark_ts
OR
(record.updated_at == watermark_ts AND record.entity_id <= watermark_id)
```

Records with a `None` timestamp (from standardization) **pass through** — they cannot be compared to a watermark, so they are included and left to the Data Quality layer to handle.

### Why composite?

A pure timestamp watermark would silently skip records that share the exact watermark timestamp.  For example, if 5 records all have `updated_at = T`, and the batch size caused 3 to be processed but 2 to be skipped, a pure timestamp watermark would commit `T` and never see the remaining 2.  The composite `(T, last_processed_id)` ensures the tie-break is explicit.

---

## 4. Watermark Advancement

```
READ records (filter by watermark)
    ↓
STANDARDIZE → SCHEMA VALIDATE → DATA QUALITY → CURATED
    ↓
RECONCILIATION
    ↓
RUN MANIFEST → SUCCESS
    ↓
COMMIT WATERMARK   ← only here

OR

FAILURE anywhere above
    ↓
❌ DO NOT COMMIT WATERMARK
    ↓
Next run retries from the last committed watermark
```

**Critical rule:** The watermark is only advanced after the entire processing chain has completed successfully.  `commit_watermark()` is a deliberate, explicit call — not automatic.

---

## 5. Idempotency

### What makes processing idempotent?

- **File-based curated output**: `persist_case_operations` writes with `open(..., "w")` — this is an overwrite. Rerunning with the same `run_id` simply replaces the same file.  No duplicate records are created.
- **Stable entity keys**: `employee_id`, `case_id`, `history_id` are immutable UUIDs.  These serve as the natural idempotency keys for future DB upsert operations (Part 10).

### Stable keys used

| Entity | Stable key |
|---|---|
| Employee | `employee_id` |
| Case | `case_id` |
| CaseHistory | `history_id` |

### Duplicate prevention

Processing the same logical records twice:
- Produces the same `filter_records_by_watermark` output (pure function — deterministic).
- Overwrites the same curated output file with identical content.
- Does NOT create duplicate logical records.

---

## 6. Incremental State Storage

State is stored in the **`pipeline_watermarks` PostgreSQL table** (created by Alembic migration `a1b2c3d4e5f6`).

| Column | Type | Description |
|---|---|---|
| `pipeline_key` | `VARCHAR(128)` PK | Logical source identifier, e.g. `"employee_incremental"` |
| `watermark_ts` | `TIMESTAMP WITH TIME ZONE` | Timestamp component of the composite watermark |
| `watermark_id` | `VARCHAR(36)` | Entity-id component (tie-breaker) |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | When the watermark was last committed |

**Why PostgreSQL and not file-based?**
Watermark state is *updated* on each successful run, not appended.  A SQL `UPDATE` is the natural primitive for this — it is atomic, consistent, and avoids file-locking concerns that arise with concurrent or retried pipeline runs.

---

## 7. Retry Behavior

1. Run A starts — reads committed watermark (e.g. `2025-01-01 / e-100`).
2. Run A selects new records, processes them.
3. Run A **fails** before `commit_watermark()` is called.
4. Committed watermark in DB is still `2025-01-01 / e-100`.
5. Run A retry starts — reads the same committed watermark.
6. Retry selects the **same records** — processes them again.
7. Retry succeeds — `commit_watermark()` is called — watermark advances.

No duplicate records are created because curated output is an overwrite by `run_id`.

---

## 8. Partial Failure Behavior

| Failure point | Watermark effect |
|---|---|
| Failure before curated persist | Watermark unchanged — retry correctly |
| Failure during curated persist | Watermark unchanged — retry correctly |
| Failure during reconciliation | Watermark unchanged — retry correctly |
| Failure after success but before watermark commit | Watermark unchanged — retry will reprocess (idempotent) |
| Failure during watermark commit (DB error) | Watermark unchanged — retry will reprocess (idempotent) |

The invariant is: **the committed watermark only advances when we can confirm the complete processing chain succeeded.**

---

## 9. Late-Arriving Data

Timestamp-based watermarks have a known limitation: if a record's `updated_at` is backdated to a time before the current watermark (e.g. a source system corrects a historical record), it will be **silently missed**.

Mitigations:
- A **lookback window** (e.g. re-process records from the last N hours before the watermark) can catch most late arrivals.  Idempotent persistence makes reprocessing safe.
- This is NOT implemented in Part 9 — it is documented as a known limitation.
- Part 9 provides the foundation; operational teams can add a lookback window without changing the core architecture.

---

## 10. Distinction from Part 10 (PySpark)

Part 9 is a **Python-native, batch-oriented, in-process** incremental strategy:
- Watermarks are managed in Python code.
- Record filtering is an in-memory list operation.
- Persistence uses synchronous SQLAlchemy.

Part 10 (PySpark) will replace or complement the processing layer with distributed execution.  The watermark table design is compatible with Spark's `foreachBatch` + JDBC pattern and does not need to change.

---

## 11. Module Reference

```
app/models/watermark.py          — PipelineWatermark SQLAlchemy model
app/pipelines/incremental.py     — IncrementalState, filter_records_by_watermark,
                                   load_watermark, commit_watermark
alembic/versions/a1b2c3d4e5f6_*  — DB migration for pipeline_watermarks table
tests/unit/test_incremental.py   — Part 9 test suite
```

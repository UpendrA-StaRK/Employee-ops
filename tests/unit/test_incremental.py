"""Unit tests for Part 9 — Incremental + Idempotent Processing.

Tests cover:
  1.  Full load (no watermark) — all records selected.
  2.  Incremental — only records newer than watermark selected.
  3.  Boundary: record exactly at watermark excluded.
  4.  Boundary: record same ts, greater id included (tie-break).
  5.  Boundary: record same ts, lesser id excluded.
  6.  Boundary: record same ts AND same id excluded.
  7.  Empty batch returns no new state.
  8.  Records with None timestamp pass through.
  9.  New watermark reflects max(updated_at, entity_id) of selected records.
  10. Watermark not advanced when no records newer than watermark exist.
  11. DB load: None returned when no row exists (first run).
  12. DB load: IncrementalState returned when row exists.
  13. DB commit: new row inserted on first commit.
  14. DB commit: existing row updated on subsequent commit.
  15. Retry: failed run does not advance watermark (caller contract).
  16. Idempotency: processing same records twice yields same new_state.
  17. Mixed batch: some records before, some after watermark.
  18. Timezone-naive timestamps handled correctly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.pipelines.incremental import (
    IncrementalState,
    commit_watermark,
    filter_records_by_watermark,
    load_watermark,
)
from app.models.watermark import PipelineWatermark


# ---------------------------------------------------------------------------
# Test fixtures — minimal records with updated_at and entity_id
# ---------------------------------------------------------------------------

def _dt(year: int, month: int, day: int, hour: int = 0) -> datetime:
    """Convenience: build a UTC-aware datetime."""
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


class FakeRecord:
    """Minimal mock of a standardized entity for filter tests."""
    def __init__(self, entity_id: str, updated_at: datetime | None):
        self.employee_id = entity_id   # matches id_field="employee_id"
        self.updated_at = updated_at


def _state(ts: datetime, entity_id: str = "") -> IncrementalState:
    return IncrementalState(
        pipeline_key="employee_incremental",
        watermark_ts=ts,
        watermark_id=entity_id,
    )


# ===========================================================================
# 1. Full load — no watermark
# ===========================================================================

class TestFullLoad:
    def test_full_load_selects_all_records(self):
        records = [FakeRecord("e1", _dt(2025, 1, 1)), FakeRecord("e2", _dt(2025, 6, 1))]
        selected, new_state = filter_records_by_watermark(
            records, state=None, id_field="employee_id"
        )
        assert selected == records

    def test_full_load_new_state_is_max_record(self):
        records = [FakeRecord("e1", _dt(2025, 1, 1)), FakeRecord("e2", _dt(2025, 6, 1))]
        _, new_state = filter_records_by_watermark(
            records, state=None, id_field="employee_id"
        )
        assert new_state is not None
        assert new_state.watermark_ts == _dt(2025, 6, 1)
        assert new_state.watermark_id == "e2"

    def test_empty_records_returns_empty_and_none_state(self):
        selected, new_state = filter_records_by_watermark(
            [], state=None, id_field="employee_id"
        )
        assert selected == []
        assert new_state is None


# ===========================================================================
# 2-6. Incremental selection and boundary semantics
# ===========================================================================

class TestIncrementalBoundarySemantics:
    WATERMARK_TS = _dt(2025, 6, 1)
    WATERMARK_ID = "e-500"

    def _run(self, records):
        return filter_records_by_watermark(
            records,
            state=_state(self.WATERMARK_TS, self.WATERMARK_ID),
            id_field="employee_id",
        )

    def test_record_newer_than_watermark_included(self):
        rec = FakeRecord("e1", _dt(2025, 6, 2))
        selected, _ = self._run([rec])
        assert selected == [rec]

    def test_record_exactly_at_watermark_excluded(self):
        """updated_at == watermark_ts AND employee_id == watermark_id → excluded."""
        rec = FakeRecord(self.WATERMARK_ID, self.WATERMARK_TS)
        selected, _ = self._run([rec])
        assert selected == []

    def test_record_older_than_watermark_excluded(self):
        rec = FakeRecord("e1", _dt(2025, 1, 1))
        selected, _ = self._run([rec])
        assert selected == []

    def test_record_same_ts_greater_id_included(self):
        """Tie-break: same watermark_ts, but entity_id > watermark_id → included."""
        rec = FakeRecord("e-999", self.WATERMARK_TS)  # "e-999" > "e-500" lexicographically
        selected, _ = self._run([rec])
        assert selected == [rec]

    def test_record_same_ts_lesser_id_excluded(self):
        """Tie-break: same watermark_ts, entity_id < watermark_id → excluded."""
        rec = FakeRecord("e-100", self.WATERMARK_TS)  # "e-100" < "e-500"
        selected, _ = self._run([rec])
        assert selected == []

    def test_mixed_batch_partial_selection(self):
        old_rec = FakeRecord("e1", _dt(2025, 1, 1))
        new_rec = FakeRecord("e2", _dt(2025, 7, 1))
        selected, _ = self._run([old_rec, new_rec])
        assert selected == [new_rec]
        assert old_rec not in selected


# ===========================================================================
# 7-8. None timestamps
# ===========================================================================

class TestNoneTimestamps:
    def test_none_timestamp_record_passes_through_on_incremental(self):
        """A record without a timestamp cannot be compared — passes through."""
        state = _state(_dt(2025, 6, 1), "e-100")
        rec = FakeRecord("e-no-ts", None)
        selected, _ = filter_records_by_watermark(
            [rec], state=state, id_field="employee_id"
        )
        assert rec in selected

    def test_none_timestamp_does_not_affect_new_watermark(self):
        """None-ts records don't drive the new watermark forward."""
        state = _state(_dt(2025, 6, 1), "e-100")
        newer_rec = FakeRecord("e-new", _dt(2025, 7, 1))
        none_ts_rec = FakeRecord("e-no-ts", None)
        _, new_state = filter_records_by_watermark(
            [none_ts_rec, newer_rec], state=state, id_field="employee_id"
        )
        assert new_state is not None
        assert new_state.watermark_ts == _dt(2025, 7, 1)
        assert new_state.watermark_id == "e-new"


# ===========================================================================
# 9-10. New watermark computation
# ===========================================================================

class TestNewWatermarkComputation:
    def test_new_state_is_max_of_selected_records(self):
        state = _state(_dt(2025, 1, 1), "e-000")
        records = [
            FakeRecord("e-a", _dt(2025, 3, 1)),
            FakeRecord("e-b", _dt(2025, 5, 1)),  # highest ts
            FakeRecord("e-c", _dt(2025, 4, 1)),
        ]
        _, new_state = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )
        assert new_state.watermark_ts == _dt(2025, 5, 1)
        assert new_state.watermark_id == "e-b"

    def test_new_state_tie_breaks_on_id_when_ts_equal(self):
        state = _state(_dt(2025, 1, 1), "e-000")
        ts = _dt(2025, 5, 1)
        records = [
            FakeRecord("e-z", ts),  # same ts, highest id
            FakeRecord("e-a", ts),
        ]
        _, new_state = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )
        assert new_state.watermark_ts == ts
        assert new_state.watermark_id == "e-z"

    def test_no_records_newer_than_watermark_returns_none_state(self):
        state = _state(_dt(2025, 12, 31), "z-999")
        records = [FakeRecord("e1", _dt(2025, 1, 1))]  # all older
        selected, new_state = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )
        assert selected == []
        assert new_state is None


# ===========================================================================
# 11-14. DB-backed load and commit (using SQLAlchemy in-memory SQLite)
# ===========================================================================

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for watermark persistence tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    # Import models package to register all tables on Base.metadata
    import app.models  # noqa: F401 — ensures all tables are registered
    from app.db.session import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class TestDatabaseWatermarkPersistence:
    def test_load_returns_none_when_no_row_exists(self, db_session):
        state = load_watermark("employee_incremental", db_session)
        assert state is None

    def test_load_returns_state_after_commit(self, db_session):
        initial = IncrementalState(
            pipeline_key="employee_incremental",
            watermark_ts=_dt(2025, 6, 1),
            watermark_id="e-500",
        )
        commit_watermark(initial, db_session)
        db_session.commit()

        loaded = load_watermark("employee_incremental", db_session)
        assert loaded is not None
        assert loaded.watermark_ts == _dt(2025, 6, 1)
        assert loaded.watermark_id == "e-500"

    def test_commit_creates_new_row_on_first_commit(self, db_session):
        state = IncrementalState(
            pipeline_key="case_incremental",
            watermark_ts=_dt(2025, 3, 1),
            watermark_id="c-1",
        )
        commit_watermark(state, db_session)
        db_session.commit()

        row = db_session.get(PipelineWatermark, "case_incremental")
        assert row is not None
        assert row.watermark_id == "c-1"

    def test_commit_updates_existing_row(self, db_session):
        state_v1 = IncrementalState(
            pipeline_key="employee_incremental",
            watermark_ts=_dt(2025, 1, 1),
            watermark_id="e-1",
        )
        commit_watermark(state_v1, db_session)
        db_session.commit()

        state_v2 = IncrementalState(
            pipeline_key="employee_incremental",
            watermark_ts=_dt(2025, 9, 1),
            watermark_id="e-999",
        )
        commit_watermark(state_v2, db_session)
        db_session.commit()

        row = db_session.get(PipelineWatermark, "employee_incremental")
        # SQLite drops tzinfo on read-back; normalize before comparing.
        row_ts = row.watermark_ts
        if row_ts.tzinfo is None:
            row_ts = row_ts.replace(tzinfo=timezone.utc)
        assert row_ts == _dt(2025, 9, 1)
        assert row.watermark_id == "e-999"

    def test_two_pipeline_keys_are_independent(self, db_session):
        commit_watermark(
            IncrementalState("employee_incremental", _dt(2025, 1, 1), "e-1"),
            db_session,
        )
        commit_watermark(
            IncrementalState("case_incremental", _dt(2025, 6, 1), "c-500"),
            db_session,
        )
        db_session.commit()

        emp = load_watermark("employee_incremental", db_session)
        case = load_watermark("case_incremental", db_session)
        assert emp.watermark_id == "e-1"
        assert case.watermark_id == "c-500"


# ===========================================================================
# 15. Retry — failed run must not advance watermark
# ===========================================================================

class TestRetryBehavior:
    def test_failed_run_does_not_advance_watermark(self, db_session):
        """Callers are responsible for only calling commit_watermark on success.
        This test verifies that if commit is never called, the watermark stays
        at its last committed position even after processing newer records."""
        initial = IncrementalState(
            pipeline_key="employee_incremental",
            watermark_ts=_dt(2025, 1, 1),
            watermark_id="e-1",
        )
        commit_watermark(initial, db_session)
        db_session.commit()

        # Simulate a run that processes new records but then FAILS before commit
        new_records = [FakeRecord("e-new", _dt(2025, 9, 1))]
        selected, candidate_state = filter_records_by_watermark(
            new_records, state=initial, id_field="employee_id"
        )
        assert len(selected) == 1
        assert candidate_state is not None

        # Simulate failure — commit_watermark is NOT called
        # Verify the committed watermark is unchanged
        still_committed = load_watermark("employee_incremental", db_session)
        assert still_committed.watermark_ts == _dt(2025, 1, 1)
        assert still_committed.watermark_id == "e-1"

    def test_retry_selects_same_records_as_original_run(self, db_session):
        """After a failed run, the next run starts from the same watermark
        and selects the same records."""
        initial = IncrementalState(
            pipeline_key="employee_incremental",
            watermark_ts=_dt(2025, 1, 1),
            watermark_id="e-1",
        )
        commit_watermark(initial, db_session)
        db_session.commit()

        new_records = [FakeRecord("e-new", _dt(2025, 9, 1))]

        # First attempt — fails (no commit)
        selected_first, _ = filter_records_by_watermark(
            new_records, state=initial, id_field="employee_id"
        )

        # Retry — reload watermark, filter again
        committed = load_watermark("employee_incremental", db_session)
        selected_retry, _ = filter_records_by_watermark(
            new_records, state=committed, id_field="employee_id"
        )

        assert selected_first == selected_retry == new_records


# ===========================================================================
# 16. Idempotency
# ===========================================================================

class TestIdempotency:
    def test_same_records_twice_produce_same_new_state(self):
        """Pure filter is deterministic — same input always yields same output."""
        state = _state(_dt(2025, 1, 1), "e-000")
        records = [FakeRecord("e-a", _dt(2025, 6, 1)), FakeRecord("e-b", _dt(2025, 3, 1))]

        _, state_first = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )
        _, state_second = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )

        assert state_first is not None
        assert state_second is not None
        assert state_first.watermark_ts == state_second.watermark_ts
        assert state_first.watermark_id == state_second.watermark_id

    def test_advancing_then_reprocessing_excludes_already_processed(self):
        """After a successful run, a re-run of the same records skips them."""
        records = [FakeRecord("e-a", _dt(2025, 6, 1))]
        state = _state(_dt(2025, 1, 1), "e-000")

        # First run
        selected, new_state = filter_records_by_watermark(
            records, state=state, id_field="employee_id"
        )
        assert len(selected) == 1
        assert new_state is not None

        # Re-run with advanced watermark — same records should be excluded
        selected_again, _ = filter_records_by_watermark(
            records, state=new_state, id_field="employee_id"
        )
        assert selected_again == []


# ===========================================================================
# 17. Timezone handling
# ===========================================================================

class TestTimezoneHandling:
    def test_naive_timestamps_treated_as_utc(self):
        """Naive datetimes on records are assumed UTC and compared correctly."""
        state = _state(_dt(2025, 6, 1), "e-000")
        # Record with a naive datetime
        naive_record = FakeRecord("e-1", datetime(2025, 7, 1))  # no tzinfo
        selected, _ = filter_records_by_watermark(
            [naive_record], state=state, id_field="employee_id"
        )
        assert naive_record in selected

    def test_naive_watermark_ts_compared_correctly(self):
        """Naive watermark_ts is treated as UTC and compared correctly."""
        naive_state = IncrementalState(
            pipeline_key="test",
            watermark_ts=datetime(2025, 6, 1),  # naive
            watermark_id="",
        )
        newer_rec = FakeRecord("e-1", _dt(2025, 7, 1))
        selected, _ = filter_records_by_watermark(
            [newer_rec], state=naive_state, id_field="employee_id"
        )
        assert newer_rec in selected

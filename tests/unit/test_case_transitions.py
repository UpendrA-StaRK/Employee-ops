"""Unit tests for Case domain business logic.

These tests exercise the transition-rule logic in isolation —
no database, no HTTP client, no fixtures needed.
"""
import pytest

from app.models.case import CaseStatus
from app.services.case import (
    ALLOWED_TRANSITIONS,
    InvalidStatusTransitionError,
    _validate_transition,
)


class TestAllowedTransitionsMap:
    """The ALLOWED_TRANSITIONS dict is the source of truth for lifecycle rules."""

    def test_all_statuses_have_an_entry(self):
        for status in CaseStatus:
            assert status in ALLOWED_TRANSITIONS, (
                f"CaseStatus.{status.name} has no entry in ALLOWED_TRANSITIONS"
            )

    def test_closed_is_terminal(self):
        assert ALLOWED_TRANSITIONS[CaseStatus.CLOSED] == set()

    def test_open_can_go_to_in_progress(self):
        assert CaseStatus.IN_PROGRESS in ALLOWED_TRANSITIONS[CaseStatus.OPEN]

    def test_open_can_go_to_closed(self):
        assert CaseStatus.CLOSED in ALLOWED_TRANSITIONS[CaseStatus.OPEN]

    def test_resolved_can_reopen_to_in_progress(self):
        assert CaseStatus.IN_PROGRESS in ALLOWED_TRANSITIONS[CaseStatus.RESOLVED]


class TestValidateTransition:
    """_validate_transition raises on illegal moves, passes on legal ones."""

    # --- Valid ---

    @pytest.mark.parametrize("old, new", [
        (CaseStatus.OPEN,        CaseStatus.IN_PROGRESS),
        (CaseStatus.OPEN,        CaseStatus.CLOSED),
        (CaseStatus.IN_PROGRESS, CaseStatus.PENDING),
        (CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED),
        (CaseStatus.PENDING,     CaseStatus.IN_PROGRESS),
        (CaseStatus.PENDING,     CaseStatus.RESOLVED),
        (CaseStatus.RESOLVED,    CaseStatus.CLOSED),
        (CaseStatus.RESOLVED,    CaseStatus.IN_PROGRESS),
    ])
    def test_valid_transition_does_not_raise(self, old, new):
        _validate_transition(old, new)  # should not raise

    # --- Invalid ---

    @pytest.mark.parametrize("old, new", [
        (CaseStatus.OPEN,     CaseStatus.RESOLVED),
        (CaseStatus.OPEN,     CaseStatus.PENDING),
        (CaseStatus.CLOSED,   CaseStatus.OPEN),
        (CaseStatus.CLOSED,   CaseStatus.IN_PROGRESS),
        (CaseStatus.CLOSED,   CaseStatus.RESOLVED),
        (CaseStatus.CLOSED,   CaseStatus.PENDING),
    ])
    def test_invalid_transition_raises(self, old, new):
        with pytest.raises(InvalidStatusTransitionError):
            _validate_transition(old, new)

    def test_error_message_contains_old_status(self):
        with pytest.raises(InvalidStatusTransitionError, match="OPEN"):
            _validate_transition(CaseStatus.OPEN, CaseStatus.RESOLVED)

    def test_error_message_contains_new_status(self):
        with pytest.raises(InvalidStatusTransitionError, match="RESOLVED"):
            _validate_transition(CaseStatus.OPEN, CaseStatus.RESOLVED)

    def test_closed_terminal_error_message(self):
        """Closed-state error message should mention 'terminal' or 'none'."""
        with pytest.raises(InvalidStatusTransitionError, match="none"):
            _validate_transition(CaseStatus.CLOSED, CaseStatus.OPEN)

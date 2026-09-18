"""Tests for Part 4: Case history and lifecycle transition rules."""
import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def employee(client):
    resp = client.post("/employees", json={
        "name": "History Tester",
        "email": "history.tester@example.com",
        "department": "QA",
        "job_title": "Tester",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def open_case(client, employee):
    resp = client.post("/cases", json={
        "employee_id": employee["employee_id"],
        "category": "GENERAL",
        "subject": "Test case",
        "description": "For lifecycle tests",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"
    return data


def _patch(client, case_id, status, comment=None):
    payload = {"status": status}
    if comment:
        payload["comment"] = comment
    return client.patch(f"/cases/{case_id}", json=payload)


# ---------------------------------------------------------------------------
# Initial creation
# ---------------------------------------------------------------------------

def test_new_case_starts_open(open_case):
    assert open_case["status"] == "OPEN"


def test_case_creation_writes_initial_history(client, open_case):
    resp = client.get(f"/cases/{open_case['case_id']}/history")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 1
    assert history[0]["old_status"] is None
    assert history[0]["new_status"] == "OPEN"
    assert history[0]["comment"] == "Case created"


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

def test_open_to_in_progress(client, open_case):
    resp = _patch(client, open_case["case_id"], "IN_PROGRESS")
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


def test_open_to_closed(client, open_case):
    resp = _patch(client, open_case["case_id"], "CLOSED")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"


def test_in_progress_to_pending(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    resp = _patch(client, open_case["case_id"], "PENDING")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"


def test_in_progress_to_resolved(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    resp = _patch(client, open_case["case_id"], "RESOLVED")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


def test_pending_to_in_progress(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "PENDING")
    resp = _patch(client, open_case["case_id"], "IN_PROGRESS")
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


def test_pending_to_resolved(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "PENDING")
    resp = _patch(client, open_case["case_id"], "RESOLVED")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


def test_resolved_to_closed(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "RESOLVED")
    resp = _patch(client, open_case["case_id"], "CLOSED")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"


def test_resolved_to_in_progress(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "RESOLVED")
    resp = _patch(client, open_case["case_id"], "IN_PROGRESS")
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------

def test_open_to_resolved_rejected(client, open_case):
    resp = _patch(client, open_case["case_id"], "RESOLVED")
    assert resp.status_code == 422
    assert "not allowed" in resp.json()["detail"]


def test_open_to_pending_rejected(client, open_case):
    resp = _patch(client, open_case["case_id"], "PENDING")
    assert resp.status_code == 422
    assert "not allowed" in resp.json()["detail"]


def test_closed_to_open_rejected(client, open_case):
    _patch(client, open_case["case_id"], "CLOSED")
    resp = _patch(client, open_case["case_id"], "OPEN")
    assert resp.status_code == 422
    assert "not allowed" in resp.json()["detail"]


def test_closed_to_in_progress_rejected(client, open_case):
    _patch(client, open_case["case_id"], "CLOSED")
    resp = _patch(client, open_case["case_id"], "IN_PROGRESS")
    assert resp.status_code == 422


def test_closed_to_resolved_rejected(client, open_case):
    _patch(client, open_case["case_id"], "CLOSED")
    resp = _patch(client, open_case["case_id"], "RESOLVED")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# History correctness
# ---------------------------------------------------------------------------

def test_status_update_creates_history(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS", comment="Starting review")
    resp = client.get(f"/cases/{open_case['case_id']}/history")
    history = resp.json()
    # creation record + one transition = 2
    assert len(history) == 2
    transition = history[1]
    assert transition["old_status"] == "OPEN"
    assert transition["new_status"] == "IN_PROGRESS"
    assert transition["comment"] == "Starting review"


def test_history_old_status_is_correct(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "PENDING")
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    assert history[1]["old_status"] == "OPEN"
    assert history[2]["old_status"] == "IN_PROGRESS"


def test_history_new_status_is_correct(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    assert history[1]["new_status"] == "IN_PROGRESS"


def test_history_comment_stored(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS", comment="HR is reviewing")
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    assert history[1]["comment"] == "HR is reviewing"


def test_history_chronological_order(client, open_case):
    _patch(client, open_case["case_id"], "IN_PROGRESS")
    _patch(client, open_case["case_id"], "PENDING")
    _patch(client, open_case["case_id"], "RESOLVED")
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    statuses = [h["new_status"] for h in history]
    assert statuses == ["OPEN", "IN_PROGRESS", "PENDING", "RESOLVED"]


def test_history_nonexistent_case_returns_404(client):
    resp = client.get("/cases/00000000-0000-0000-0000-000000000000/history")
    assert resp.status_code == 404


def test_no_duplicate_history_on_non_status_update(client, open_case):
    # Update only subject — no history record should be created
    client.patch(f"/cases/{open_case['case_id']}", json={"subject": "Updated subject"})
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    # Only the initial creation record
    assert len(history) == 1


# ---------------------------------------------------------------------------
# Transaction behaviour
# ---------------------------------------------------------------------------

def test_invalid_transition_does_not_modify_case(client, open_case):
    """A rejected transition must not change the case status."""
    resp = _patch(client, open_case["case_id"], "RESOLVED")
    assert resp.status_code == 422

    # Case must still be OPEN
    case = client.get(f"/cases/{open_case['case_id']}").json()
    assert case["status"] == "OPEN"


def test_invalid_transition_does_not_create_history(client, open_case):
    """A rejected transition must not leave any partial history record."""
    _patch(client, open_case["case_id"], "RESOLVED")  # invalid
    history = client.get(f"/cases/{open_case['case_id']}/history").json()
    # Only the initial creation record should exist
    assert len(history) == 1

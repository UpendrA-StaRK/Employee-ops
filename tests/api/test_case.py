import pytest

@pytest.fixture
def test_employee(client):
    """Fixture to create a test employee."""
    response = client.post(
        "/employees",
        json={
            "name": "Test Employee",
            "email": "test.case@example.com",
            "department": "IT",
            "job_title": "Support Engineer",
        },
    )
    assert response.status_code == 201
    return response.json()

def test_create_case(client, test_employee):
    response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "ACCESS",
            "subject": "Lost VPN Access",
            "description": "I can no longer connect to the VPN.",
            "priority": "HIGH"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == test_employee["employee_id"]
    assert data["category"] == "ACCESS"
    assert data["subject"] == "Lost VPN Access"
    assert data["description"] == "I can no longer connect to the VPN."
    assert data["priority"] == "HIGH"
    assert data["status"] == "OPEN"  # default
    assert "case_id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_case_invalid_employee(client):
    response = client.post(
        "/cases",
        json={
            "employee_id": "00000000-0000-0000-0000-000000000000",
            "category": "GENERAL",
            "subject": "Question",
            "description": "Test",
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_existing_case(client, test_employee):
    create_response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "PAYROLL",
            "subject": "Missing paycheck",
            "description": "Did not receive salary this month.",
            "priority": "URGENT"
        },
    )
    case_id = create_response.json()["case_id"]

    response = client.get(f"/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["category"] == "PAYROLL"

def test_get_nonexistent_case(client):
    response = client.get("/cases/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Case with ID 00000000-0000-0000-0000-000000000000 not found"

def test_list_and_filter_cases(client, test_employee):
    # Create multiple cases
    client.post(
        "/cases",
        json={"employee_id": test_employee["employee_id"], "category": "LEAVE", "subject": "Vacation", "description": "Need time off", "priority": "LOW"}
    )
    client.post(
        "/cases",
        json={"employee_id": test_employee["employee_id"], "category": "LEAVE", "subject": "Sick leave", "description": "Feeling unwell", "priority": "MEDIUM"}
    )
    client.post(
        "/cases",
        json={"employee_id": test_employee["employee_id"], "category": "BENEFITS", "subject": "Health Insurance", "description": "Update dependents"}
    )
    
    # 1. List all cases
    response = client.get("/cases")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

    # 2. Filter by employee_id
    response = client.get(f"/cases?employee_id={test_employee['employee_id']}")
    data = response.json()
    assert all(c["employee_id"] == test_employee["employee_id"] for c in data)

    # 3. Filter by category
    response = client.get(f"/cases?employee_id={test_employee['employee_id']}&category=LEAVE")
    data = response.json()
    assert len(data) == 2
    assert all(c["category"] == "LEAVE" for c in data)

    # 4. Filter by priority
    response = client.get(f"/cases?employee_id={test_employee['employee_id']}&priority=LOW")
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority"] == "LOW"

def test_update_case(client, test_employee):
    create_response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "GENERAL",
            "subject": "Need new mouse",
            "description": "My mouse is broken.",
        },
    )
    case_id = create_response.json()["case_id"]

    response = client.patch(
        f"/cases/{case_id}",
        json={
            "status": "IN_PROGRESS",
            "priority": "HIGH"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["priority"] == "HIGH"
    
    # Verify other fields remain unchanged
    assert data["category"] == "GENERAL"
    assert data["subject"] == "Need new mouse"

def test_update_invalid_fields(client, test_employee):
    create_response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "GENERAL",
            "subject": "Test Case",
            "description": "Desc",
        },
    )
    case_id = create_response.json()["case_id"]

    # First move to IN_PROGRESS (valid from OPEN)
    client.patch(f"/cases/{case_id}", json={"status": "IN_PROGRESS"})

    # Now PATCH with an extra employee_id field (should be ignored) + valid status
    response = client.patch(
        f"/cases/{case_id}",
        json={
            "employee_id": "00000000-0000-0000-0000-000000000000",
            "status": "RESOLVED"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    # Ensure employee_id did NOT change
    assert data["employee_id"] == test_employee["employee_id"]

def test_invalid_status_and_priority(client, test_employee):
    response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "GENERAL",
            "subject": "Test",
            "description": "Test",
            "status": "INVALID_STATUS",
            "priority": "SUPER_HIGH"
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"] == ["body", "status"] for err in errors)
    assert any(err["loc"] == ["body", "priority"] for err in errors)

def test_invalid_category(client, test_employee):
    response = client.post(
        "/cases",
        json={
            "employee_id": test_employee["employee_id"],
            "category": "NOT_A_CATEGORY",
            "subject": "Test",
            "description": "Test",
        },
    )
    assert response.status_code == 422

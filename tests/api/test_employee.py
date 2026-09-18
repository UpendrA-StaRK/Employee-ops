import pytest

def test_create_employee(client):
    response = client.post(
        "/employees",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "department": "Engineering",
            "job_title": "Software Engineer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert data["department"] == "Engineering"
    assert data["job_title"] == "Software Engineer"
    assert data["status"] == "ACTIVE"
    assert "employee_id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_existing_employee(client):
    create_response = client.post(
        "/employees",
        json={
            "name": "John Smith",
            "email": "john@example.com",
            "department": "HR",
            "job_title": "Manager",
        },
    )
    employee_id = create_response.json()["employee_id"]

    response = client.get(f"/employees/{employee_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == employee_id
    assert data["name"] == "John Smith"

def test_get_nonexistent_employee(client):
    response = client.get("/employees/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Employee with ID 00000000-0000-0000-0000-000000000000 not found"

def test_create_duplicate_email(client):
    payload = {
        "name": "Alice Cooper",
        "email": "alice@example.com",
        "department": "Sales",
        "job_title": "Director",
    }
    # First creation should succeed
    response1 = client.post("/employees", json=payload)
    assert response1.status_code == 201

    # Second creation should fail with conflict
    response2 = client.post("/employees", json=payload)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

def test_create_invalid_employee(client):
    # Missing required field 'email' and 'name'
    response = client.post(
        "/employees",
        json={
            "department": "IT",
            "job_title": "Support",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    # Check that it identifies missing fields
    assert any(err["loc"] == ["body", "name"] for err in errors)
    assert any(err["loc"] == ["body", "email"] for err in errors)

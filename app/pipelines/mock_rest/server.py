"""Lightweight mock REST source server for development and testing.

This provides a simulated enterprise reference service exposing
department and job-title reference data relevant to the Employee
Operations domain.

Usage (development):
    uv run python -m app.pipelines.mock_rest.server

Usage (tests):
    Use the FastAPI TestClient or respx mocking — do not spin up a real
    process in unit tests.

This mock exists only to provide a realistic REST ingestion target.
It is NOT a production service.
"""
from fastapi import FastAPI

mock_app = FastAPI(title="Mock Reference Service", version="1.0.0")


# ---------------------------------------------------------------------------
# Static reference data — deterministic and stable for tests.
# In a real enterprise system this would come from a reference database.
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    {"code": "HR", "name": "Human Resources"},
    {"code": "ENG", "name": "Engineering"},
    {"code": "FIN", "name": "Finance"},
    {"code": "OPS", "name": "Operations"},
    {"code": "LEGAL", "name": "Legal"},
    {"code": "IT", "name": "Information Technology"},
    {"code": "SALES", "name": "Sales"},
    {"code": "MKTG", "name": "Marketing"},
]

JOB_TITLES = [
    {"code": "SWE", "department_code": "ENG", "title": "Software Engineer"},
    {"code": "SRE", "department_code": "ENG", "title": "Site Reliability Engineer"},
    {"code": "HRC", "department_code": "HR", "title": "HR Coordinator"},
    {"code": "HRM", "department_code": "HR", "title": "HR Manager"},
    {"code": "FIN_AN", "department_code": "FIN", "title": "Financial Analyst"},
    {"code": "OPS_MG", "department_code": "OPS", "title": "Operations Manager"},
    {"code": "IT_SUP", "department_code": "IT", "title": "IT Support Specialist"},
    {"code": "SALES_R", "department_code": "SALES", "title": "Sales Representative"},
]


@mock_app.get("/departments")
def list_departments() -> list[dict]:
    """Return all valid department reference codes."""
    return DEPARTMENTS


@mock_app.get("/job-titles")
def list_job_titles() -> list[dict]:
    """Return all valid job title reference codes."""
    return JOB_TITLES


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="127.0.0.1", port=8001)

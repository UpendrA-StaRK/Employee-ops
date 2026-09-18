"""Case endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.case import CaseStatus, CaseCategory, CasePriority
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.schemas.case_history import CaseHistoryResponse
from app.services.case import (
    case_service,
    CaseNotFoundError,
    EmployeeNotFoundError,
    InvalidStatusTransitionError,
)

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """
    Create a new case for an employee.

    The case always starts with status **OPEN**.
    An initial history record is created automatically.
    """
    try:
        case = case_service.create_case(db, case_in)
        return CaseResponse.model_validate(case)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "",
    response_model=List[CaseResponse],
    summary="List cases",
)
def list_cases(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    case_status: Optional[CaseStatus] = Query(None, alias="status", description="Filter by case status"),
    category: Optional[CaseCategory] = Query(None, description="Filter by case category"),
    priority: Optional[CasePriority] = Query(None, description="Filter by case priority"),
    db: Session = Depends(get_db),
) -> List[CaseResponse]:
    """List cases with optional filtering by employee, status, category, or priority."""
    cases = case_service.list_cases(
        db,
        employee_id=employee_id,
        status=case_status,
        category=category,
        priority=priority,
    )
    return [CaseResponse.model_validate(c) for c in cases]


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Get a case by ID",
)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Retrieve a case by its ID."""
    try:
        case = case_service.get_case(db, case_id)
        return CaseResponse.model_validate(case)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Update a case",
)
def update_case(
    case_id: str,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """
    Update mutable fields on an existing case.

    When **status** changes, the transition is validated against lifecycle rules
    and a history record is created automatically.

    Include an optional **comment** to annotate the reason for a status change.

    **Allowed transitions:**
    - `OPEN` → `IN_PROGRESS`, `CLOSED`
    - `IN_PROGRESS` → `PENDING`, `RESOLVED`
    - `PENDING` → `IN_PROGRESS`, `RESOLVED`
    - `RESOLVED` → `CLOSED`, `IN_PROGRESS`
    - `CLOSED` → *(terminal — no further transitions)*
    """
    try:
        updated = case_service.update_case(db, case_id, case_in)
        return CaseResponse.model_validate(updated)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{case_id}/history",
    response_model=List[CaseHistoryResponse],
    summary="Get case history",
)
def get_case_history(
    case_id: str,
    db: Session = Depends(get_db),
) -> List[CaseHistoryResponse]:
    """
    Return the status history for a case in chronological order (oldest first).

    Returns 404 if the case does not exist.

    > **Note:** The `changed_by` field currently defaults to `"system"` as a
    > placeholder. Real user identity will be populated once authentication
    > is introduced in a later week.
    """
    try:
        history = case_service.get_case_history(db, case_id)
        return [CaseHistoryResponse.model_validate(h) for h in history]
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

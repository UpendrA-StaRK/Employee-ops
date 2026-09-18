"""Employee endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.services.employee import (
    employee_service,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Create a new employee record."""
    try:
        employee = employee_service.create_employee(db, employee_in)
        return EmployeeResponse.model_validate(employee)
    except EmployeeAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get an employee by ID",
)
def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    """Retrieve an employee by their ID."""
    try:
        employee = employee_service.get_employee(db, employee_id)
        return EmployeeResponse.model_validate(employee)
    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

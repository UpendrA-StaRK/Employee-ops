"""Employee service."""
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.employee import employee_repo
from app.schemas.employee import EmployeeCreate


class EmployeeAlreadyExistsError(Exception):
    """Raised when trying to create an employee with an existing email."""


class EmployeeNotFoundError(Exception):
    """Raised when an employee is not found."""


class EmployeeService:
    """Business logic for the Employee domain."""

    def create_employee(self, db: Session, employee_in: EmployeeCreate) -> Employee:
        if employee_repo.get_by_email(db, email=employee_in.email):
            raise EmployeeAlreadyExistsError(f"Employee with email {employee_in.email} already exists")
        return employee_repo.create(db, employee_in)

    def get_employee(self, db: Session, employee_id: str) -> Employee:
        employee = employee_repo.get(db, employee_id)
        if not employee:
            raise EmployeeNotFoundError(f"Employee with ID {employee_id} not found")
        return employee


# Module-level instance for simple dependency injection
employee_service = EmployeeService()

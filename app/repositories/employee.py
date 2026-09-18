"""Employee repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate


class EmployeeRepository:
    """Repository for Employee model. Handles only DB access."""

    def create(self, db: Session, employee_in: EmployeeCreate) -> Employee:
        db_employee = Employee(
            name=employee_in.name,
            email=employee_in.email,
            department=employee_in.department,
            job_title=employee_in.job_title,
            status=employee_in.status,
        )
        db.add(db_employee)
        db.flush()
        db.refresh(db_employee)
        return db_employee

    def get(self, db: Session, employee_id: str) -> Employee | None:
        return db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        ).scalar_one_or_none()

    def get_by_email(self, db: Session, email: str) -> Employee | None:
        return db.execute(
            select(Employee).where(Employee.email == email)
        ).scalar_one_or_none()


# Module-level instance for simple dependency injection
employee_repo = EmployeeRepository()

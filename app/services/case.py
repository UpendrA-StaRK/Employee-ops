"""Case service."""
from typing import Sequence
from sqlalchemy.orm import Session
import logging

from app.models.case import Case, CaseStatus, CaseCategory, CasePriority
from app.repositories.case import case_repo
from app.repositories.employee import employee_repo
from app.schemas.case import CaseCreate, CaseUpdate

logger = logging.getLogger(__name__)


class CaseNotFoundError(Exception):
    """Raised when a case is not found."""


class EmployeeNotFoundError(Exception):
    """Raised when the referenced employee is not found."""


class CaseService:
    """Business logic for the Case domain."""

    def create_case(self, db: Session, case_in: CaseCreate) -> Case:
        # Business Rule 1: Verify the referenced employee exists
        employee = employee_repo.get(db, case_in.employee_id)
        if not employee:
            logger.warning("Failed to create case: Employee %s not found", case_in.employee_id)
            raise EmployeeNotFoundError(f"Employee with ID {case_in.employee_id} not found")
        
        case = case_repo.create(db, case_in)
        logger.info("Created case %s for employee %s", case.case_id, case.employee_id)
        return case

    def get_case(self, db: Session, case_id: str) -> Case:
        case = case_repo.get(db, case_id)
        if not case:
            logger.warning("Failed to retrieve case: Case %s not found", case_id)
            raise CaseNotFoundError(f"Case with ID {case_id} not found")
        return case

    def list_cases(
        self,
        db: Session,
        *,
        employee_id: str | None = None,
        status: CaseStatus | None = None,
        category: CaseCategory | None = None,
        priority: CasePriority | None = None,
    ) -> Sequence[Case]:
        return case_repo.list(
            db,
            employee_id=employee_id,
            status=status,
            category=category,
            priority=priority,
        )

    def update_case(self, db: Session, case_id: str, case_in: CaseUpdate) -> Case:
        db_case = self.get_case(db, case_id)
        
        # We don't need manual validation for status/priority since Pydantic 
        # handles Enum validation at the API layer. The updated_at field is 
        # handled by SQLAlchemy automatically on update.
        
        updated_case = case_repo.update(db, db_case, case_in)
        logger.info("Updated case %s", updated_case.case_id)
        return updated_case


# Module-level instance for simple dependency injection
case_service = CaseService()

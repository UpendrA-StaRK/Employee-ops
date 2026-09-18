"""Case repository."""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus, CaseCategory, CasePriority
from app.schemas.case import CaseCreate, CaseUpdate


class CaseRepository:
    """Repository for Case model. Handles only DB access."""

    def create(self, db: Session, case_in: CaseCreate) -> Case:
        db_case = Case(
            employee_id=case_in.employee_id,
            category=case_in.category,
            subject=case_in.subject,
            description=case_in.description,
            status=case_in.status,
            priority=case_in.priority,
        )
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return db_case

    def get(self, db: Session, case_id: str) -> Case | None:
        return db.execute(
            select(Case).where(Case.case_id == case_id)
        ).scalar_one_or_none()

    def list(
        self,
        db: Session,
        *,
        employee_id: str | None = None,
        status: CaseStatus | None = None,
        category: CaseCategory | None = None,
        priority: CasePriority | None = None,
    ) -> Sequence[Case]:
        query = select(Case)
        
        if employee_id:
            query = query.where(Case.employee_id == employee_id)
        if status:
            query = query.where(Case.status == status)
        if category:
            query = query.where(Case.category == category)
        if priority:
            query = query.where(Case.priority == priority)
            
        return db.execute(query.order_by(Case.created_at.desc())).scalars().all()

    def update(self, db: Session, db_case: Case, case_in: CaseUpdate) -> Case:
        update_data = case_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_case, field, value)
            
        db.commit()
        db.refresh(db_case)
        return db_case


# Module-level instance for simple dependency injection
case_repo = CaseRepository()

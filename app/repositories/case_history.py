"""Case History repository."""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case_history import CaseHistory
from app.models.case import CaseStatus


class CaseHistoryRepository:
    """Handles all DB access for CaseHistory records."""

    def create(
        self,
        db: Session,
        *,
        case_id: str,
        old_status: CaseStatus | None,
        new_status: CaseStatus,
        comment: str | None,
        changed_by: str,
    ) -> CaseHistory:
        record = CaseHistory(
            case_id=case_id,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            changed_by=changed_by,
        )
        db.add(record)
        # Caller owns the commit — flush so we get the ID if needed
        db.flush()
        db.refresh(record)
        return record

    def list_for_case(self, db: Session, case_id: str) -> Sequence[CaseHistory]:
        """Return history records for a case, oldest first."""
        return (
            db.execute(
                select(CaseHistory)
                .where(CaseHistory.case_id == case_id)
                .order_by(CaseHistory.created_at.asc())
            )
            .scalars()
            .all()
        )


case_history_repo = CaseHistoryRepository()

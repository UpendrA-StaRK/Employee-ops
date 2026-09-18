"""Case service — owns business logic and transaction boundaries."""
from typing import Sequence
from sqlalchemy.orm import Session
import logging

from app.models.case import Case, CaseStatus, CaseCategory, CasePriority
from app.models.case_history import CaseHistory
from app.repositories.case import case_repo
from app.repositories.case_history import case_history_repo
from app.repositories.employee import employee_repo
from app.schemas.case import CaseCreate, CaseUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class CaseNotFoundError(Exception):
    """Raised when a case is not found."""


class EmployeeNotFoundError(Exception):
    """Raised when the referenced employee is not found."""


class InvalidStatusTransitionError(Exception):
    """Raised when the requested status transition is not permitted."""


# ---------------------------------------------------------------------------
# Transition rules — explicit, easy to read, easy to extend
# ---------------------------------------------------------------------------

# Maps each status to the set of statuses that it may transition TO.
ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.OPEN:        {CaseStatus.IN_PROGRESS, CaseStatus.CLOSED},
    CaseStatus.IN_PROGRESS: {CaseStatus.PENDING, CaseStatus.RESOLVED},
    CaseStatus.PENDING:     {CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED},
    CaseStatus.RESOLVED:    {CaseStatus.CLOSED, CaseStatus.IN_PROGRESS},
    CaseStatus.CLOSED:      set(),  # Terminal state — no further transitions
}


def _validate_transition(old_status: CaseStatus, new_status: CaseStatus) -> None:
    """Raise InvalidStatusTransitionError if the transition is not allowed."""
    allowed = ALLOWED_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(
            f"Status transition from '{old_status}' to '{new_status}' is not allowed. "
            f"Allowed transitions from '{old_status}': "
            f"{sorted(s.value for s in allowed) or ['none (terminal state)']}"
        )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class CaseService:
    """Business logic for the Case domain. Owns transaction boundaries."""

    def create_case(self, db: Session, case_in: CaseCreate) -> Case:
        """Create a case with an initial OPEN status and record its history."""
        # Business rule: the referenced employee must exist
        employee = employee_repo.get(db, case_in.employee_id)
        if not employee:
            logger.warning(
                "create_case failed: employee_id=%s not found", case_in.employee_id
            )
            raise EmployeeNotFoundError(
                f"Employee with ID {case_in.employee_id} not found"
            )

        # Force status to OPEN on creation regardless of what was sent
        case_in = case_in.model_copy(update={"status": CaseStatus.OPEN})
        case = case_repo.create(db, case_in)

        # Audit: initial creation → old_status is None, new_status is OPEN
        case_history_repo.create(
            db,
            case_id=case.case_id,
            old_status=None,
            new_status=CaseStatus.OPEN,
            comment="Case created",
            changed_by="system",
        )

        db.commit()
        db.refresh(case)
        logger.info("case_created case_id=%s employee_id=%s", case.case_id, case.employee_id)
        return case

    def get_case(self, db: Session, case_id: str) -> Case:
        case = case_repo.get(db, case_id)
        if not case:
            logger.warning("get_case failed: case_id=%s not found", case_id)
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

    def update_case(
        self,
        db: Session,
        case_id: str,
        case_in: CaseUpdate,
        changed_by: str = "system",
    ) -> Case:
        """
        Update a case.

        If status is changing:
          1. Validate the transition against ALLOWED_TRANSITIONS.
          2. Apply the update.
          3. Write a CaseHistory record.
          4. Commit atomically — the case update and history record are one
             logical operation. If either fails the transaction rolls back.

        If only non-status fields are changing, update normally without
        creating a history record.
        """
        db_case = self.get_case(db, case_id)
        old_status = db_case.status
        new_status = case_in.status

        status_is_changing = new_status is not None and new_status != old_status

        if status_is_changing:
            _validate_transition(old_status, new_status)

        # Apply all field updates (flush only — no commit yet)
        case_repo.update(db, db_case, case_in)

        if status_is_changing:
            case_history_repo.create(
                db,
                case_id=db_case.case_id,
                old_status=old_status,
                new_status=new_status,
                comment=case_in.comment if hasattr(case_in, "comment") else None,
                changed_by=changed_by,
            )
            logger.info(
                "case_status_transition case_id=%s old_status=%s new_status=%s changed_by=%s",
                db_case.case_id, old_status, new_status, changed_by,
            )

        # Single commit — case update + history in one transaction
        db.commit()
        db.refresh(db_case)
        return db_case

    def get_case_history(self, db: Session, case_id: str) -> Sequence[CaseHistory]:
        """Return history for a case, verifying the case exists first."""
        # Raises CaseNotFoundError if not found
        self.get_case(db, case_id)
        return case_history_repo.list_for_case(db, case_id)


# Module-level singleton
case_service = CaseService()

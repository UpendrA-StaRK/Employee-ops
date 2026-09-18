"""Case SQLAlchemy model."""
import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.employee import Employee


class CaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CaseCategory(str, enum.Enum):
    LEAVE = "LEAVE"
    PAYROLL = "PAYROLL"
    BENEFITS = "BENEFITS"
    ACCESS = "ACCESS"
    GENERAL = "GENERAL"


class Case(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category: Mapped[CaseCategory] = mapped_column(
        Enum(CaseCategory, name="case_category_enum"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum"), nullable=False, default=CaseStatus.OPEN
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority, name="case_priority_enum"), nullable=False, default=CasePriority.MEDIUM
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Optional relationship, useful if we need to load the employee directly
    # employee: Mapped["Employee"] = relationship("Employee")

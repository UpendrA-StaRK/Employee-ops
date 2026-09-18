"""Case History SQLAlchemy model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.case import CaseStatus


class CaseHistory(Base):
    __tablename__ = "case_history"

    history_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    old_status: Mapped[CaseStatus | None] = mapped_column(
        Enum(CaseStatus, name="case_status_enum", create_type=False), nullable=True
    )
    new_status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum", create_type=False), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Optional relationship to Case
    # case: Mapped["Case"] = relationship("Case", back_populates="history")

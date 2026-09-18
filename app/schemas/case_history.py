"""Case History schema."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.case import CaseStatus


class CaseHistoryResponse(BaseModel):
    history_id: str
    case_id: str
    old_status: Optional[CaseStatus]
    new_status: CaseStatus
    comment: Optional[str]
    changed_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

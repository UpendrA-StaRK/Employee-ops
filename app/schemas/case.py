"""Case schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.models.case import CaseStatus, CasePriority, CaseCategory


class CaseBase(BaseModel):
    category: CaseCategory
    subject: str = Field(..., max_length=255)
    description: str
    status: CaseStatus = Field(default=CaseStatus.OPEN)
    priority: CasePriority = Field(default=CasePriority.MEDIUM)


class CaseCreate(CaseBase):
    employee_id: str


class CaseUpdate(BaseModel):
    category: Optional[CaseCategory] = None
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    comment: Optional[str] = None  # Optional annotation for status transitions


class CaseResponse(CaseBase):
    case_id: str
    employee_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

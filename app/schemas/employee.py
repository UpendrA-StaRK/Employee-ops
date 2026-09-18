"""Employee schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr = Field(..., max_length=255)
    department: str = Field(..., max_length=100)
    job_title: str = Field(..., max_length=100)
    status: str = Field(default="ACTIVE", max_length=50)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    employee_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

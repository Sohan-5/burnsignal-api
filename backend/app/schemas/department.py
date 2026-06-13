from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class DepartmentCreate(BaseModel):
    name: str
    lead_user_id: Optional[UUID] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    lead_user_id: Optional[UUID] = None

class DepartmentOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    lead_user_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

class DepartmentSummary(DepartmentOut):
    project_count: int = 0
    total_budget: float = 0.0
    total_spent: float = 0.0

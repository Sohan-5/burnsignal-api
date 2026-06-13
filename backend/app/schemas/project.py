from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional, Literal

DurationType = Literal['sprint', 'medium', 'program']
ProjectStatus = Literal['active', 'completed', 'archived']

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    duration_type: DurationType
    start_date: date
    end_date: date

    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    duration_type: Optional[DurationType] = None
    end_date: Optional[date] = None

class ProjectOut(BaseModel):
    id: UUID
    org_id: UUID
    department_id: Optional[UUID]
    name: str
    description: Optional[str]
    status: ProjectStatus
    duration_type: DurationType
    start_date: date
    end_date: date
    created_at: datetime
    class Config:
        from_attributes = True

class ProjectDetail(ProjectOut):
    days_remaining: int = 0
    elapsed_pct: float = 0.0
    budget: Optional[dict] = None
    current_tier: Optional[str] = None

class BurnSummary(BaseModel):
    project_id: UUID
    total_budget: float
    total_spent: float
    utilization_pct: float
    burn_ratio: float
    headcount_spent: float
    tools_spent: float
    contractors_spent: float
    days_remaining: int
    currency: str = 'USD'

class BurnTimeline(BaseModel):
    project_id: UUID
    entries: list[dict]  # [{date, daily_cost, cumulative_cost}]

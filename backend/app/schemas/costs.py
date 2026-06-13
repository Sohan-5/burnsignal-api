from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional, Literal

ReasonAdded = Literal['deadline_pressure', 'skill_gap', 'scope_expansion', 'planned']

class ToolCostCreate(BaseModel):
    tool_name: str
    monthly_cost: float
    active_from: date
    active_to: Optional[date] = None
    notes: Optional[str] = None

class ToolCostUpdate(BaseModel):
    monthly_cost: Optional[float] = None
    active_to: Optional[date] = None
    notes: Optional[str] = None

class ToolCostOut(ToolCostCreate):
    id: UUID
    project_id: UUID
    department_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True

class ContractorCostCreate(BaseModel):
    contractor_name: str
    role: Optional[str] = None
    daily_rate: float
    start_date: date
    end_date: Optional[date] = None
    reason_added: ReasonAdded = 'planned'
    notes: Optional[str] = None

class ContractorCostUpdate(BaseModel):
    end_date: Optional[date] = None
    daily_rate: Optional[float] = None
    reason_added: Optional[ReasonAdded] = None
    notes: Optional[str] = None

class ContractorCostOut(ContractorCostCreate):
    id: UUID
    project_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

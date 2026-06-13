from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional, Literal

PhaseStatus = Literal['pending', 'active', 'completed']

class PhaseCreate(BaseModel):
    name: str
    phase_order: int = 1
    planned_start: date
    planned_end: date
    budget_allocation_pct: float  # e.g. 25.0 = 25%

    @field_validator('budget_allocation_pct')
    @classmethod
    def valid_pct(cls, v):
        if not 0 < v <= 100:
            raise ValueError('budget_allocation_pct must be between 0 and 100')
        return v

class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    budget_allocation_pct: Optional[float] = None
    status: Optional[PhaseStatus] = None

class PhaseOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    phase_order: int
    planned_start: date
    planned_end: date
    actual_start: Optional[date]
    actual_end: Optional[date]
    budget_allocation_pct: float
    status: PhaseStatus
    slip_days: int = 0
    class Config:
        from_attributes = True

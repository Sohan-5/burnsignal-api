from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

class BudgetCreate(BaseModel):
    total_amount: float
    currency: str = 'USD'
    headcount_pct: float = 60.0
    tools_pct: float = 15.0
    contractors_pct: float = 20.0
    contingency_pct: float = 5.0

    @field_validator('headcount_pct', 'tools_pct', 'contractors_pct', 'contingency_pct')
    @classmethod
    def valid_pct(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v

class BudgetUpdate(BaseModel):
    total_amount: Optional[float] = None
    headcount_pct: Optional[float] = None
    tools_pct: Optional[float] = None
    contractors_pct: Optional[float] = None
    contingency_pct: Optional[float] = None

class BudgetOut(BudgetCreate):
    id: UUID
    project_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

class BudgetUtilization(BaseModel):
    total_budget: float
    total_spent: float
    utilization_pct: float
    burn_ratio: float
    days_remaining: int
    timeline_elapsed_pct: float
    by_category: dict  # {headcount, tools, contractors, contingency} -> {budget, spent, pct}
    currency: str = 'USD'

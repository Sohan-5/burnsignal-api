from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional

class ProjectBurnCard(BaseModel):
    project_id: UUID
    name: str
    status: str
    duration_type: str
    budget: float
    spent: float
    utilization_pct: float
    burn_ratio: float
    predicted_breach_date: Optional[date]
    confidence_score: float
    tier: str
    days_remaining: int
    top_pressure_signal: Optional[str]

class EngLeadDashboard(BaseModel):
    org_id: UUID
    projects: list[ProjectBurnCard]
    total_budget: float
    total_spent: float
    projects_at_risk: int   # burn_ratio > 1.2
    projects_critical: int  # burn_ratio > 1.5
    avg_confidence: float

class PMDashboard(BaseModel):
    org_id: UUID
    projects: list[ProjectBurnCard]
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    avg_velocity_pct: float
    sprint_cost_this_week: float

class FinanceDashboard(BaseModel):
    org_id: UUID
    total_budget_all: float
    total_spent_all: float
    overrun_flags: list[dict]   # projects where burn_ratio > 1.3
    by_department: list[dict]   # [{dept_name, budget, spent, pct}]
    mom_spend: list[dict]        # [{month, spend}] last 6 months

class MemberDashboard(BaseModel):
    user_id: UUID
    hours_this_week: float
    hours_this_month: float
    my_projects: list[dict]
    recent_entries: list[dict]

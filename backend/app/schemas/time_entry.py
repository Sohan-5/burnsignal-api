from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional, Literal

EntrySource = Literal['manual', 'trello', 'jira', 'github', 'linear']

class TimeEntryCreate(BaseModel):
    entry_date: date
    hours: float
    hourly_rate: float
    phase_id: Optional[UUID] = None
    notes: Optional[str] = None

    @field_validator('hours')
    @classmethod
    def positive_hours(cls, v):
        if v <= 0:
            raise ValueError('hours must be positive')
        return v

class TimeEntryUpdate(BaseModel):
    entry_date: Optional[date] = None
    hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    phase_id: Optional[UUID] = None
    notes: Optional[str] = None

class TimeEntryOut(BaseModel):
    id: UUID
    project_id: UUID
    user_id: Optional[UUID]
    phase_id: Optional[UUID]
    entry_date: date
    hours: float
    hourly_rate: float
    cost: float
    source: EntrySource
    notes: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class TimeEntrySummary(BaseModel):
    total_hours: float
    total_cost: float
    by_user: list[dict]    # [{user_id, name, hours, cost}]
    by_phase: list[dict]   # [{phase_id, name, hours, cost}]
    by_source: dict        # {manual: N, trello: N, ...}
    by_week: list[dict]    # [{week, hours, cost}]

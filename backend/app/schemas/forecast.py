from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional, Literal

ForecastTier = Literal['1', '2', '3a', '3b']

class SignalValue(BaseModel):
    name: str
    value: float       # 0.0 - 1.0 normalized
    weight: float      # signal weight in the model
    contribution: float  # weight * value = contribution to multiplier
    label: str         # human readable label

class ForecastResult(BaseModel):
    id: UUID
    project_id: UUID
    snapshot_at: datetime
    tier: ForecastTier
    data_points: int
    baseline_forecast: Optional[float]
    pressure_multiplier: float
    final_forecast: Optional[float]
    predicted_breach_date: Optional[date]
    confidence_score: float
    daily_burn_rate: Optional[float]
    burn_ratio: Optional[float]
    signal_values: dict
    signals: list[SignalValue] = []
    class Config:
        from_attributes = True

class ForecastHistory(BaseModel):
    project_id: UUID
    snapshots: list[ForecastResult]
    breach_date_trend: list[dict]  # [{date, predicted_breach_date}] for drift chart

class TierConfig(BaseModel):
    tier: ForecastTier
    smoothing_window_days: int
    signal_sensitivity: float
    horizon_unit: Literal['days', 'weeks', 'months']
    confidence_ceiling: float
    model_name: str

"""Selects forecast tier based on project state."""
from dataclasses import dataclass
from typing import Literal

@dataclass
class TierConfig:
    tier: Literal[1, 2, "3a", "3b"]
    smoothing_window_days: int
    signal_sensitivity: float
    horizon_unit: Literal["days", "weeks", "months"]
    confidence_ceiling: float

def select_tier(duration_type: str, data_points: int, historical_count: int) -> TierConfig:
    if data_points < 7:
        return TierConfig(1, data_points, 0.3, "days", 0.3)
    if duration_type == "sprint":
        return TierConfig(2, 3, 0.9, "days", 0.65)
    if duration_type == "medium":
        return TierConfig("3a", 7, 0.6, "weeks", 0.8)
    return TierConfig("3b", 28, 0.3, "months", 0.95)

def get_signal_weights(tier: TierConfig) -> dict:
    if tier.tier == 2:
        return {"velocity_gap": 0.35, "overdue_ratio": 0.30, "scope_creep_rate": 0.15, "headcount_delta": 0.20}
    if tier.tier == "3a":
        return {"phase_slip_days": 0.30, "timeline_pressure": 0.25, "velocity_gap": 0.20, "headcount_delta": 0.25}
    if tier.tier == "3b":
        return {"phase_slip_days": 0.35, "budget_acceleration": 0.30, "timeline_pressure": 0.20, "headcount_delta": 0.15}
    return {}

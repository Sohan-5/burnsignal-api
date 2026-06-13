"""Combines baseline + pressure into final ForecastResult. Multiplier clamped to [1.0, 2.5]."""
from dataclasses import dataclass
from datetime import date, timedelta, datetime
from typing import Optional

@dataclass
class ForecastResult:
    tier: str
    baseline_forecast: float
    pressure_multiplier: float
    final_forecast: float
    predicted_breach_date: Optional[date]
    confidence_score: float
    signal_values: dict
    snapshot_at: str

def combine(baseline: dict, signals: dict, weights: dict, budget: float) -> ForecastResult:
    pressure_sum = sum(weights.get(k, 0) * v for k, v in signals.items())
    multiplier = max(1.0, min(2.5, 1.0 + pressure_sum))
    final_forecast = (baseline.get("level", 0) or 0) * multiplier
    trend = baseline.get("trend", 0)
    breach = None
    if trend and trend > 0:
        remaining = budget - baseline.get("level", 0)
        if remaining > 0:
            breach = date.today() + timedelta(days=int(remaining / trend / multiplier))
        else:
            breach = date.today()
    confidence = compute_confidence(baseline.get("tier", 1), baseline.get("data_points", 0), _signal_stability(signals))
    return ForecastResult(
        tier=str(baseline.get("tier", 1)),
        baseline_forecast=round(baseline.get("level", 0), 2),
        pressure_multiplier=round(multiplier, 3),
        final_forecast=round(final_forecast, 2),
        predicted_breach_date=breach,
        confidence_score=round(confidence, 2),
        signal_values={k: round(v, 3) for k, v in signals.items()},
        snapshot_at=datetime.utcnow().isoformat(),
    )

def compute_confidence(tier, data_points: int, signal_stability: float) -> float:
    ceiling = {1: 0.30, 2: 0.65, "3a": 0.80, "3b": 0.95}.get(tier, 0.30)
    return ceiling * (0.6 * min(1.0, data_points / 30) + 0.4 * signal_stability)

def _signal_stability(signals: dict) -> float:
    if not signals: return 0.5
    vals = list(signals.values())
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    return max(0.0, 1.0 - variance * 4)

"""Time series baseline models (weighted LR, Holt's, Holt-Winters)."""
import numpy as np
from datetime import date, timedelta

def weighted_linear(series: list, budget: float, decay: float = 0.1) -> dict:
    n = len(series)
    if n < 2:
        return {"breach_date": None, "slope": 0, "confidence": 0.1}
    x = np.arange(n, dtype=float)
    y = np.array(series, dtype=float)
    weights = np.exp(-decay * (n - 1 - x))
    W = np.diag(weights)
    X = np.column_stack([np.ones(n), x])
    beta = np.linalg.lstsq(X.T @ W @ X, X.T @ W @ y, rcond=None)[0]
    alpha, slope = beta
    if slope <= 0:
        return {"breach_date": None, "slope": slope, "confidence": 0.15}
    days_to_breach = (budget - alpha) / slope
    breach_date = date.today() + timedelta(days=int(days_to_breach - n))
    return {"breach_date": breach_date, "slope": slope, "confidence": 0.25}

def holts_smoothing(series: list, budget: float, alpha: float = 0.3, beta: float = 0.1) -> dict:
    if len(series) < 3:
        return weighted_linear(series, budget)
    level = series[0]
    trend = series[1] - series[0]
    for val in series[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    if trend <= 0:
        return {"breach_date": None, "level": level, "trend": trend, "confidence": 0.3}
    steps = (budget - level) / trend
    return {"breach_date": date.today() + timedelta(days=int(steps)), "level": level, "trend": trend, "confidence": 0.6}

def holt_winters(
    series: list,
    budget: float,
    period: int = 14,
    alpha: float = 0.3,
    beta: float = 0.1,
    gamma: float = 0.1,
    max_horizon_days: int = 3650,
) -> dict:
    """Additive Holt-Winters (triple exponential smoothing) on DAILY burn.

    `series` is the CUMULATIVE spend series (one point per day). Seasonality
    shows up in daily spend, not in the ever-rising cumulative line, so we
    difference the series into daily burn, fit level / trend / seasonal factors
    on that, then project daily burn forward and accumulate it until the budget
    is reached.

    Returned keys follow the contract used by combiner.combine():
      level  -> current cumulative spend
      trend  -> deseasonalized daily burn rate (spend per day)
    plus breach_date (seasonally projected), seasonal_factors and confidence.

    Needs two full seasonal cycles of daily burn; otherwise falls back to
    holts_smoothing().
    """
    # daily burn has len(series) - 1 points, so require 2 * period + 1 series points
    if period < 2 or len(series) < period * 2 + 1:
        return holts_smoothing(series, budget, alpha, beta)

    cumulative = [float(v) for v in series]
    # clip small negative corrections so a bad entry cannot flip the model
    daily = [max(0.0, cumulative[i + 1] - cumulative[i]) for i in range(len(cumulative) - 1)]
    n = len(daily)

    # Initialise from the first two cycles
    first = daily[:period]
    second = daily[period:2 * period]
    level = sum(first) / period
    trend = (sum(second) / period - level) / period
    season = [d - level for d in first]

    for t in range(period, n):
        idx = t % period
        prev_level = level
        level = alpha * (daily[t] - season[idx]) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        season[idx] = gamma * (daily[t] - level) + (1 - gamma) * season[idx]

    current_spend = cumulative[-1]
    deseasonalized_burn = max(0.0, level + trend)

    breach_date = None
    if current_spend >= budget:
        breach_date = date.today()
    else:
        projected = current_spend
        for h in range(1, max_horizon_days + 1):
            projected += max(0.0, level + h * trend + season[(n - 1 + h) % period])
            if projected >= budget:
                breach_date = date.today() + timedelta(days=h)
                break

    return {
        "breach_date": breach_date,
        "level": current_spend,
        "trend": deseasonalized_burn,
        "seasonal_factors": [round(s, 4) for s in season],
        "confidence": 0.7,
    }

def compute_burn_ratio(spent: float, budget: float, elapsed_pct: float) -> float:
    if elapsed_pct <= 0:
        return 1.0
    return (spent / budget) / elapsed_pct

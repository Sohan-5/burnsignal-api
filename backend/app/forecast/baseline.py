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

def holt_winters(series: list, budget: float, period: int = 14, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.1) -> dict:
    if len(series) < period * 2:
        return holts_smoothing(series, budget, alpha, beta)
    # TODO: implement full seasonality component
    return holts_smoothing(series, budget, alpha, beta)

def compute_burn_ratio(spent: float, budget: float, elapsed_pct: float) -> float:
    if elapsed_pct <= 0:
        return 1.0
    return (spent / budget) / elapsed_pct

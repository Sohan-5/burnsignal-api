"""Loads historical weights. Falls back to ISBSG seed data for new orgs."""
import json
from pathlib import Path

SEED_PATH = Path(__file__).parents[3] / "seed-data" / "isbsg_priors.json"

def load_priors(org_id: str, duration_type: str, historical_projects: list) -> dict:
    if len(historical_projects) >= 3:
        return fit_weights(historical_projects, duration_type)
    return load_seed_priors(duration_type)

def load_seed_priors(duration_type: str) -> dict:
    if not SEED_PATH.exists():
        return _default_weights(duration_type)
    with open(SEED_PATH) as f:
        data = json.load(f)
    return data.get(duration_type, _default_weights(duration_type))

def fit_weights(historical_projects: list, duration_type: str) -> dict:
    # TODO: implement OLS regression against historical overrun data
    return load_seed_priors(duration_type)

def phase_cost_prior(duration_type: str, phase_idx: int, total_phases: int) -> float:
    priors = load_seed_priors(duration_type)
    curves = priors.get("phase_cost_curves", {})
    return curves.get(f"{phase_idx+1}_of_{total_phases}", (phase_idx + 1) / total_phases)

def _default_weights(duration_type: str) -> dict:
    if duration_type == "sprint":
        return {"velocity_gap": 0.35, "overdue_ratio": 0.30, "scope_creep_rate": 0.15, "headcount_delta": 0.20}
    if duration_type == "medium":
        return {"phase_slip_days": 0.30, "timeline_pressure": 0.25, "velocity_gap": 0.20, "headcount_delta": 0.25}
    return {"phase_slip_days": 0.35, "budget_acceleration": 0.30, "timeline_pressure": 0.20, "headcount_delta": 0.15}

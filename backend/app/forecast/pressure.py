"""Computes project health pressure signals. All return float 0.0-1.0."""

def compute_all_signals(project: dict, tasks: list, contractors: list, snapshots: list, tier_config) -> dict:
    signals = {}
    if tier_config.tier in (2, "3a", "3b"):
        signals["velocity_gap"] = velocity_gap(tasks)
        signals["overdue_ratio"] = overdue_ratio(tasks)
        signals["headcount_delta"] = headcount_delta(contractors)
        signals["timeline_pressure"] = timeline_pressure(project)
    if tier_config.tier in ("3a", "3b"):
        signals["phase_slip_days"] = phase_slip_days(project.get("phases", []))
        signals["scope_creep_rate"] = scope_creep_rate(tasks, project.get("baseline_task_count", 0))
    if tier_config.tier == "3b":
        signals["budget_acceleration"] = budget_acceleration(snapshots)
    return signals

def velocity_gap(tasks: list, window_days: int = 7) -> float:
    planned = sum(1 for t in tasks if t.get("planned_completion_in_window"))
    actual = sum(1 for t in tasks if t.get("completed_in_window"))
    if planned == 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - actual / planned))

def overdue_ratio(tasks: list) -> float:
    open_tasks = [t for t in tasks if t.get("status") != "completed"]
    if not open_tasks:
        return 0.0
    return sum(1 for t in open_tasks if t.get("is_overdue")) / len(open_tasks)

def scope_creep_rate(tasks: list, baseline_count: int) -> float:
    baseline_count = baseline_count or 0
    if baseline_count == 0:
        return 0.0
    return min(1.0, max(0, len(tasks) - baseline_count) / baseline_count)

def headcount_delta(contractors: list, window_days: int = 14) -> float:
    weights = {"deadline_pressure": 1.0, "skill_gap": 0.6, "scope_expansion": 0.4, "planned": 0.1}
    score = sum(weights.get(c.get("reason_added", "planned"), 0.1) for c in contractors if c.get("added_in_window"))
    return min(1.0, score / 3)

def phase_slip_days(phases: list) -> float:
    total_slip = sum(max(0, (p.get("actual_start_day", 0) - p.get("planned_start_day", 0))) for p in phases if p.get("actual_start_day") is not None)
    duration = sum(p.get("planned_duration_days", 1) for p in phases) or 1
    return min(1.0, total_slip / duration)

def timeline_pressure(project: dict) -> float:
    e = float(project.get("elapsed_pct", 0) or 0)
    if e < 0.5: return e * 0.2
    if e < 0.8: return 0.1 + (e - 0.5) * 0.6
    return 0.28 + (e - 0.8) * 3.6

def budget_acceleration(snapshots: list) -> float:
    if len(snapshots) < 3:
        return 0.0
    rates = [s.get("daily_burn_rate", 0) for s in snapshots[-3:]]
    deltas = [rates[i+1] - rates[i] for i in range(len(rates)-1)]
    return min(1.0, max(0.0, (deltas[-1] - deltas[0]) / (rates[0] + 1e-9)))

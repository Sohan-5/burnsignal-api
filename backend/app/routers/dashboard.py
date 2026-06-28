from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.project import Project
from app.models.project_phase import ProjectPhase
from app.models.contractor_cost import ContractorCost
from app.models.tool_cost import ToolCost
from app.forecast.store import get_latest
from datetime import date, timedelta
import uuid

router = APIRouter()

SIGNAL_LABELS = {
    "velocity_gap": "Velocity Gap",
    "overdue_ratio": "Overdue Ratio",
    "scope_creep_rate": "Scope Creep Rate",
    "headcount_delta": "Headcount Delta",
    "timeline_pressure": "Timeline Pressure",
    "phase_slip_days": "Phase Slip",
    "budget_acceleration": "Budget Acceleration",
}

SIGNAL_DETAILS = {
    "velocity_gap": "Planned vs actual task completion rate",
    "overdue_ratio": "Share of open tasks past due",
    "scope_creep_rate": "Task count growth vs baseline",
    "headcount_delta": "Recent contractor additions",
    "timeline_pressure": "Elapsed time vs project duration",
    "phase_slip_days": "Schedule slippage across phases",
    "budget_acceleration": "Recent change in daily burn rate",
}

@router.get("/{org_id}/projects/{project_id}")
async def get_project_detail(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    try:
        org_uuid = uuid.UUID(org_id)
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Project)
        .options(selectinload(Project.budget), selectinload(Project.time_entries), selectinload(Project.phases), selectinload(Project.contractor_costs), selectinload(Project.tool_costs))
        .where(Project.org_id == org_uuid)
        .where(Project.id == proj_uuid)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_budget = float(project.budget.total_amount) if project.budget else 0
    total_spent = sum(float(e.cost) for e in project.time_entries)
    days_remaining = (project.end_date - date.today()).days if project.end_date else 0

    snapshot = await get_latest(project_id, db)

    if snapshot:
        burn_ratio = float(snapshot["burn_ratio"])
        forecast = {
            "predicted_breach": str(snapshot["predicted_breach_date"]) if snapshot["predicted_breach_date"] else None,
            "confidence": round(float(snapshot["confidence_score"]) * 100),
            "tier": f"T{snapshot['tier']}",
        }
        signal_values = snapshot["signal_values"] or {}
        pressure_signals = [
            {
                "name": SIGNAL_LABELS.get(k, k),
                "intensity": round(v * 100),
                "detail": SIGNAL_DETAILS.get(k, ""),
            }
            for k, v in signal_values.items()
        ]
    else:
        burn_ratio = round(total_spent / total_budget, 2) if total_budget > 0 else 0
        forecast = {"predicted_breach": None, "confidence": 0, "tier": "—"}
        pressure_signals = [
            {"name": "Velocity Gap", "intensity": 0, "detail": "No forecast run yet"},
            {"name": "Timeline Pressure", "intensity": max(0, min(100, int((1 - days_remaining/180) * 100))), "detail": f"{days_remaining} days remaining"},
        ]

    today = date.today()
    timeline = []
    cumulative = 0
    for i in range(-30, 31):
        d = today + timedelta(days=i)
        if d < today:
            day_entries = [e for e in project.time_entries if e.entry_date == d]
            cumulative += sum(float(e.cost) for e in day_entries)
            timeline.append({"date": str(d), "actual": round(cumulative, 2), "forecast": None, "band": None})
        else:
            daily_burn = total_spent / 30 if total_spent > 0 else total_budget / max(days_remaining, 1)
            forecast_val = round(total_spent + daily_burn * (i + 1), 2)
            timeline.append({"date": str(d), "actual": None, "forecast": forecast_val, "band": [round(forecast_val * 0.9, 2), round(forecast_val * 1.1, 2)]})

    sorted_phases = sorted(project.phases, key=lambda p: p.phase_order)

    return {
        "id": str(project.id), "name": project.name, "status": project.status,
        "duration_type": project.duration_type, "start_date": str(project.start_date),
        "end_date": str(project.end_date), "days_remaining": days_remaining,
        "total_budget": total_budget, "total_spent": round(total_spent, 2), "burn_ratio": burn_ratio,
        "forecast": forecast,
        "pressure_signals": pressure_signals, "timeline": timeline,
        "phases": [
            {
                "name": p.name,
                "phase_order": p.phase_order,
                "budget_pct": float(p.budget_allocation_pct),
                "status": p.status,
                "planned_start": str(p.planned_start),
                "planned_end": str(p.planned_end),
                "actual_start": str(p.actual_start) if p.actual_start else None,
                "actual_end": str(p.actual_end) if p.actual_end else None,
            }
            for p in sorted_phases
        ],
        "time_entries": [{"id": str(e.id), "hours": float(e.hours), "cost": float(e.cost), "entry_date": str(e.entry_date), "notes": e.notes or ""} for e in project.time_entries[-10:]],
        "contractors": [{"id": str(c.id), "contractor_name": c.contractor_name, "role": c.role, "daily_rate": float(c.daily_rate), "start_date": str(c.start_date), "end_date": str(c.end_date) if c.end_date else None, "reason_added": c.reason_added, "notes": c.notes or ""} for c in project.contractor_costs],
        "tool_costs": [{"id": str(t.id), "tool_name": t.tool_name, "monthly_cost": float(t.monthly_cost), "active_from": str(t.active_from), "active_to": str(t.active_to) if t.active_to else None, "notes": t.notes or ""} for t in project.tool_costs],
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.historical_project import HistoricalProject
from app.models.project import Project
from app.forecast.store import get_latest
import uuid

router = APIRouter()


@router.get("/{org_id}/historical")
async def list_historical(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(HistoricalProject).where(
            (HistoricalProject.org_id == org_uuid) | (HistoricalProject.org_id.is_(None))
        )
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(h.id),
            "source": h.source,
            "duration_type": h.duration_type,
            "project_type": h.project_type,
            "planned_budget": float(h.planned_budget) if h.planned_budget else None,
            "actual_budget": float(h.actual_budget) if h.actual_budget else None,
            "overrun_pct": float(h.overrun_pct) if h.overrun_pct else None,
            "team_size": h.team_size,
            "duration_days": h.duration_days,
        }
        for h in rows
    ]


@router.post("/{org_id}/historical/archive/{project_id}")
async def archive_project(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.budget), selectinload(Project.time_entries))
        .where(Project.id == uuid.UUID(project_id))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    planned_budget = float(project.budget.total_amount) if project.budget else 0
    actual_spent = sum(float(e.cost) for e in project.time_entries)
    overrun_pct = round((actual_spent - planned_budget) / planned_budget, 4) if planned_budget > 0 else 0

    duration_days = (project.end_date - project.start_date).days if project.start_date and project.end_date else None

    snapshot = await get_latest(project_id, db)
    signal_values = snapshot["signal_values"] if snapshot else {}

    h = HistoricalProject(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        source="org",
        duration_type=project.duration_type,
        project_type=None,
        planned_budget=planned_budget,
        actual_budget=actual_spent,
        overrun_pct=overrun_pct,
        team_size=None,
        duration_days=duration_days,
        phase_cost_breakdown={},
        signal_values_at_overrun=signal_values or {},
    )
    db.add(h)
    await db.commit()
    await db.refresh(h)

    return {
        "id": str(h.id),
        "status": "archived",
        "planned_budget": planned_budget,
        "actual_budget": actual_spent,
        "overrun_pct": overrun_pct,
    }


@router.post("/{org_id}/historical/import-seed")
async def import_seed_data(org_id: str, db: AsyncSession = Depends(get_db)):
    """Seed baseline historical projects for forecast calibration (org-agnostic benchmark data)."""
    seed_records = [
        {"source": "isbsg", "duration_type": "sprint", "project_type": "web_app", "planned_budget": 80000, "actual_budget": 92000, "team_size": 4, "duration_days": 45},
        {"source": "isbsg", "duration_type": "medium", "project_type": "mobile_app", "planned_budget": 180000, "actual_budget": 205000, "team_size": 6, "duration_days": 120},
        {"source": "isbsg", "duration_type": "program", "project_type": "platform", "planned_budget": 450000, "actual_budget": 510000, "team_size": 12, "duration_days": 270},
        {"source": "nasa", "duration_type": "program", "project_type": "infrastructure", "planned_budget": 600000, "actual_budget": 720000, "team_size": 15, "duration_days": 300},
        {"source": "isbsg", "duration_type": "sprint", "project_type": "internal_tool", "planned_budget": 50000, "actual_budget": 51500, "team_size": 3, "duration_days": 30},
    ]

    created = []
    for rec in seed_records:
        overrun_pct = round((rec["actual_budget"] - rec["planned_budget"]) / rec["planned_budget"], 4)
        h = HistoricalProject(
            id=uuid.uuid4(),
            org_id=None,
            source=rec["source"],
            duration_type=rec["duration_type"],
            project_type=rec["project_type"],
            planned_budget=rec["planned_budget"],
            actual_budget=rec["actual_budget"],
            overrun_pct=overrun_pct,
            team_size=rec["team_size"],
            duration_days=rec["duration_days"],
            phase_cost_breakdown={},
            signal_values_at_overrun={},
        )
        db.add(h)
        created.append(rec["source"])

    await db.commit()
    return {"status": "imported", "count": len(created)}

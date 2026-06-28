from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.forecast.forecast import run_forecast
from pydantic import BaseModel
from datetime import date
import uuid

router = APIRouter()


class TimeEntryCreate(BaseModel):
    project_id: str
    hours: float
    cost: float
    entry_date: date
    description: str = ""


@router.get("/{org_id}/time-entries")
async def list_time_entries(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(TimeEntry, Project.name)
        .join(Project)
        .where(Project.org_id == org_uuid)
        .order_by(TimeEntry.entry_date.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "id": str(e.id),
            "project_id": str(e.project_id),
            "project_name": project_name,
            "hours": float(e.hours),
            "cost": float(e.cost),
            "entry_date": str(e.entry_date),
            "description": e.notes or "",
        }
        for e, project_name in rows
    ]


@router.get("/{org_id}/time-entries/summary")
async def time_entries_summary(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(Project.id, Project.name, TimeEntry)
        .join(TimeEntry, TimeEntry.project_id == Project.id)
        .where(Project.org_id == org_uuid)
    )
    rows = result.all()

    summary = {}
    for project_id, project_name, entry in rows:
        key = str(project_id)
        if key not in summary:
            summary[key] = {
                "project_id": key,
                "project_name": project_name,
                "total_hours": 0.0,
                "total_cost": 0.0,
                "entry_count": 0,
            }
        summary[key]["total_hours"] += float(entry.hours)
        summary[key]["total_cost"] += float(entry.cost)
        summary[key]["entry_count"] += 1

    for v in summary.values():
        v["total_hours"] = round(v["total_hours"], 2)
        v["total_cost"] = round(v["total_cost"], 2)

    return list(summary.values())


@router.post("/{org_id}/time-entries")
async def create_time_entry(org_id: str, entry: TimeEntryCreate, db: AsyncSession = Depends(get_db)):
    hourly_rate = round(entry.cost / entry.hours, 2) if entry.hours > 0 else 150.0
    te = TimeEntry(
        id=uuid.uuid4(),
        project_id=uuid.UUID(entry.project_id),
        hours=entry.hours,
        hourly_rate=hourly_rate,
        entry_date=entry.entry_date,
        notes=entry.description,
        source="manual",
    )
    db.add(te)
    await db.commit()
    await db.refresh(te)
    forecast_updated = False
    try:
        await run_forecast(entry.project_id, db)
        forecast_updated = True
    except Exception:
        pass
    return {
        "id": str(te.id),
        "hours": float(te.hours),
        "cost": float(te.cost),
        "forecast_updated": forecast_updated,
    }

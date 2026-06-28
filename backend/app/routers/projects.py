from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.project import Project
from app.models.budget import Budget
from app.forecast.store import get_latest
from datetime import date
import uuid

router = APIRouter()

@router.get("/{org_id}/projects")
async def list_projects(org_id: str, db: AsyncSession = Depends(get_db)):
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        org_uuid = None

    query = select(Project).options(selectinload(Project.budget), selectinload(Project.time_entries))
    if org_uuid:
        query = query.where(Project.org_id == org_uuid)

    result = await db.execute(query)
    projects = result.scalars().all()

    output = []
    for p in projects:
        total_budget = float(p.budget.total_amount) if p.budget else 0
        spent = sum(float(e.cost) for e in p.time_entries)

        snapshot = await get_latest(str(p.id), db)
        if snapshot:
            burn_ratio = float(snapshot["burn_ratio"])
            predicted_breach = str(snapshot["predicted_breach_date"]) if snapshot["predicted_breach_date"] else None
            confidence = round(float(snapshot["confidence_score"]) * 100)
        else:
            elapsed_pct = 0
            if p.start_date and p.end_date:
                total_days = (p.end_date - p.start_date).days or 1
                elapsed_days = (date.today() - p.start_date).days
                elapsed_pct = max(0.01, min(1.0, elapsed_days / total_days))
            burn_ratio = round((spent / total_budget) / elapsed_pct, 2) if total_budget > 0 else 0
            predicted_breach = None
            confidence = 0

        output.append({
            "id": str(p.id),
            "name": p.name,
            "status": p.status,
            "duration_type": p.duration_type,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "total_budget": total_budget,
            "spent": round(spent, 2),
            "burn_ratio": burn_ratio,
            "predicted_breach": predicted_breach,
            "confidence": confidence,
        })

    return output


@router.get("/{org_id}/projects/{project_id}/tasks")
async def get_project_tasks(
    org_id: str,
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    org_uuid = uuid.UUID(org_id)
    project_uuid = uuid.UUID(project_id)

    # Verify project belongs to org
    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_uuid,
            Project.org_id == org_uuid,
        )
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found.")

    from app.models.imported_task import ImportedTask
    result = await db.execute(
        select(ImportedTask)
        .where(ImportedTask.project_id == project_uuid)
        .order_by(ImportedTask.is_overdue.desc(), ImportedTask.due_date.asc())
    )
    tasks = result.scalars().all()

    return {
        "tasks": [
            {
                "title": t.title,
                "status": t.status,
                "due_date": str(t.due_date) if t.due_date else None,
                "is_overdue": t.is_overdue,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ]
    }

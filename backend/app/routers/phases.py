from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.project import Project
from app.models.imported_task import ImportedTask
import uuid

router = APIRouter()


@router.get("/{org_id}/sprints-summary")
async def sprints_summary(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(Project)
        .where(Project.org_id == org_uuid)
    )
    projects = result.scalars().all()

    sprint_projects = []
    for p in projects:
        task_result = await db.execute(
            select(ImportedTask).where(ImportedTask.project_id == p.id)
        )
        tasks = task_result.scalars().all()

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        overdue_tasks = len([t for t in tasks if t.is_overdue])
        completion_pct = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

        sprint_projects.append({
            "id": str(p.id),
            "name": p.name,
            "status": p.status,
            "duration_type": p.duration_type,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_pct": completion_pct,
            "velocity": completed_tasks,
            "planned_points": total_tasks,
            "completed_points": completed_tasks,
        })

    return {
        "sprint_projects": sprint_projects,
        "total_projects": len(sprint_projects),
    }

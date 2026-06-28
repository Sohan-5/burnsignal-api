from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.project import Project
from app.models.budget import Budget
from app.models.department import Department
from datetime import date
from collections import defaultdict
import uuid

router = APIRouter()


@router.get("/{org_id}/budget-summary")
async def budget_summary(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(Project).options(
            selectinload(Project.budget),
            selectinload(Project.time_entries),
            selectinload(Project.department),
        )
        .where(Project.org_id == org_uuid)
    )
    projects = result.scalars().all()

    rows = []
    dept_totals = defaultdict(lambda: {"budget": 0.0, "spent": 0.0, "projects": 0})
    monthly = defaultdict(float)

    for p in projects:
        b = p.budget
        total = float(b.total_amount) if b else 0
        spent = sum(float(e.cost) for e in p.time_entries)
        burn_ratio = round(spent / total, 2) if total > 0 else 0

        rows.append({
            "project_id": str(p.id),
            "project_name": p.name,
            "status": p.status,
            "duration_type": p.duration_type,
            "total_budget": total,
            "spent": round(spent, 2),
            "remaining": round(total - spent, 2),
            "burn_ratio": burn_ratio,
            "overrun": burn_ratio > 1.0,
        })

        dept_name = p.department.name if p.department else "Unassigned"
        dept_totals[dept_name]["budget"] += total
        dept_totals[dept_name]["spent"] += spent
        dept_totals[dept_name]["projects"] += 1

        for e in p.time_entries:
            month_key = e.entry_date.strftime("%Y-%m")
            monthly[month_key] += float(e.cost)

    department_breakdown = [
        {
            "department": name,
            "total_budget": round(v["budget"], 2),
            "spent": round(v["spent"], 2),
            "utilization_pct": round((v["spent"] / v["budget"]) * 100) if v["budget"] > 0 else 0,
            "project_count": v["projects"],
        }
        for name, v in dept_totals.items()
    ]

    today = date.today()
    last_6_months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        key = f"{y}-{m:02d}"
        last_6_months.append({
            "month": key,
            "month_label": date(y, m, 1).strftime("%b"),
            "spend": round(monthly.get(key, 0.0), 2),
        })

    return {
        "total_budget": sum(r["total_budget"] for r in rows),
        "total_spent": round(sum(r["spent"] for r in rows), 2),
        "total_remaining": round(sum(r["remaining"] for r in rows), 2),
        "projects": rows,
        "department_breakdown": department_breakdown,
        "monthly_spend": last_6_months,
    }

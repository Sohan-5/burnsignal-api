from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.contractor_cost import ContractorCost
from app.models.tool_cost import ToolCost
from app.models.project import Project
from pydantic import BaseModel
from datetime import date
from typing import Optional
import uuid

router = APIRouter()


class ContractorCreate(BaseModel):
    project_id: str
    contractor_name: str
    role: Optional[str] = None
    daily_rate: float
    start_date: date
    end_date: Optional[date] = None
    reason_added: str = "planned"
    notes: Optional[str] = None


class ToolCostCreate(BaseModel):
    project_id: str
    department_id: Optional[str] = None
    tool_name: str
    monthly_cost: float
    active_from: date
    active_to: Optional[date] = None
    notes: Optional[str] = None


@router.get("/{org_id}/contractors")
async def list_contractors(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(ContractorCost, Project.name)
        .join(Project)
        .where(Project.org_id == org_uuid)
        .order_by(ContractorCost.start_date.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(c.id),
            "project_id": str(c.project_id),
            "project_name": project_name,
            "contractor_name": c.contractor_name,
            "role": c.role,
            "daily_rate": float(c.daily_rate),
            "start_date": str(c.start_date),
            "end_date": str(c.end_date) if c.end_date else None,
            "reason_added": c.reason_added,
            "notes": c.notes or "",
        }
        for c, project_name in rows
    ]


@router.post("/{org_id}/contractors")
async def create_contractor(org_id: str, payload: ContractorCreate, db: AsyncSession = Depends(get_db)):
    c = ContractorCost(
        id=uuid.uuid4(),
        project_id=uuid.UUID(payload.project_id),
        contractor_name=payload.contractor_name,
        role=payload.role,
        daily_rate=payload.daily_rate,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason_added=payload.reason_added,
        notes=payload.notes,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": str(c.id), "contractor_name": c.contractor_name}


@router.put("/{org_id}/contractors/{contractor_id}")
async def update_contractor(org_id: str, contractor_id: str, payload: ContractorCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContractorCost).where(ContractorCost.id == uuid.UUID(contractor_id)))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Contractor not found")
    c.contractor_name = payload.contractor_name
    c.role = payload.role
    c.daily_rate = payload.daily_rate
    c.start_date = payload.start_date
    c.end_date = payload.end_date
    c.reason_added = payload.reason_added
    c.notes = payload.notes
    await db.commit()
    return {"id": str(c.id), "status": "updated"}


@router.get("/{org_id}/tool-costs")
async def list_tool_costs(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(ToolCost, Project.name)
        .join(Project)
        .where(Project.org_id == org_uuid)
        .order_by(ToolCost.active_from.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(t.id),
            "project_id": str(t.project_id),
            "project_name": project_name,
            "tool_name": t.tool_name,
            "monthly_cost": float(t.monthly_cost),
            "active_from": str(t.active_from),
            "active_to": str(t.active_to) if t.active_to else None,
            "notes": t.notes or "",
        }
        for t, project_name in rows
    ]


@router.post("/{org_id}/tool-costs")
async def create_tool_cost(org_id: str, payload: ToolCostCreate, db: AsyncSession = Depends(get_db)):
    t = ToolCost(
        id=uuid.uuid4(),
        project_id=uuid.UUID(payload.project_id),
        department_id=uuid.UUID(payload.department_id) if payload.department_id else None,
        tool_name=payload.tool_name,
        monthly_cost=payload.monthly_cost,
        active_from=payload.active_from,
        active_to=payload.active_to,
        notes=payload.notes,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "tool_name": t.tool_name}


@router.put("/{org_id}/tool-costs/{tool_cost_id}")
async def update_tool_cost(org_id: str, tool_cost_id: str, payload: ToolCostCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ToolCost).where(ToolCost.id == uuid.UUID(tool_cost_id)))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tool cost not found")
    t.tool_name = payload.tool_name
    t.monthly_cost = payload.monthly_cost
    t.active_from = payload.active_from
    t.active_to = payload.active_to
    t.notes = payload.notes
    await db.commit()
    return {"id": str(t.id), "status": "updated"}

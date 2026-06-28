from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.department import Department
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()


class DepartmentCreate(BaseModel):
    name: str
    lead_user_id: Optional[str] = None


@router.get("/{org_id}/departments")
async def list_departments(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(select(Department).where(Department.org_id == org_uuid))
    depts = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "lead_user_id": str(d.lead_user_id) if d.lead_user_id else None,
        }
        for d in depts
    ]


@router.post("/{org_id}/departments")
async def create_department(org_id: str, payload: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    d = Department(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=payload.name,
        lead_user_id=uuid.UUID(payload.lead_user_id) if payload.lead_user_id else None,
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return {"id": str(d.id), "name": d.name}


@router.get("/{org_id}/departments/{dept_id}")
async def get_department(org_id: str, dept_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).where(Department.id == uuid.UUID(dept_id)))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found")
    return {
        "id": str(d.id),
        "name": d.name,
        "lead_user_id": str(d.lead_user_id) if d.lead_user_id else None,
    }


@router.put("/{org_id}/departments/{dept_id}")
async def update_department(org_id: str, dept_id: str, payload: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).where(Department.id == uuid.UUID(dept_id)))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found")
    d.name = payload.name
    d.lead_user_id = uuid.UUID(payload.lead_user_id) if payload.lead_user_id else None
    await db.commit()
    return {"id": str(d.id), "status": "updated"}


@router.delete("/{org_id}/departments/{dept_id}")
async def delete_department(org_id: str, dept_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).where(Department.id == uuid.UUID(dept_id)))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found")
    await db.delete(d)
    await db.commit()
    return {"status": "deleted"}

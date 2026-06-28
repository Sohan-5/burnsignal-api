from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.organization import Organization
import uuid

router = APIRouter()

@router.post("")
async def create_org(name: str, db: AsyncSession = Depends(get_db)):
    org = Organization(id=uuid.uuid4(), name=name, slug=name.lower().replace(" ", "-"))
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return {"id": str(org.id), "name": org.name, "slug": org.slug}

@router.get("")
async def list_orgs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization))
    orgs = result.scalars().all()
    return [{"id": str(o.id), "name": o.name} for o in orgs]

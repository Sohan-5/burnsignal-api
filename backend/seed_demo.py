import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.organization import Organization
from app.models.project import Project
from app.models.budget import Budget
import uuid
from datetime import date
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with AsyncSessionLocal() as db:
        org = Organization(id=uuid.uuid4(), name="Demo Corp", slug="demo-corp", plan="pro")
        db.add(org)
        await db.flush()

        projects = [
            Project(id=uuid.uuid4(), org_id=org.id, name="API Platform v2",
                    status="active", duration_type="sprint",
                    start_date=date(2026,1,1), end_date=date(2026,6,30)),
            Project(id=uuid.uuid4(), org_id=org.id, name="Mobile Redesign",
                    status="active", duration_type="medium",
                    start_date=date(2026,2,1), end_date=date(2026,8,31)),
            Project(id=uuid.uuid4(), org_id=org.id, name="Data Pipeline",
                    status="active", duration_type="program",
                    start_date=date(2026,3,1), end_date=date(2026,12,31)),
        ]
        for p in projects:
            db.add(p)
        await db.flush()

        budgets = [
            Budget(id=uuid.uuid4(), project_id=projects[0].id, total_amount=150000),
            Budget(id=uuid.uuid4(), project_id=projects[1].id, total_amount=200000),
            Budget(id=uuid.uuid4(), project_id=projects[2].id, total_amount=500000),
        ]
        for b in budgets:
            db.add(b)

        await db.commit()
        print(f"Org ID: {org.id}")
        print(f"Projects: {[p.name for p in projects]}")

asyncio.run(seed())

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.department import Department
from app.models.contractor_cost import ContractorCost
from app.models.tool_cost import ToolCost
import uuid
from datetime import date, timedelta
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

ORG_ID = "fb82c0b3-2153-4393-8169-8169ea907d73"
API_PROJECT = "5ee235b5-0d3c-4665-ab4f-a264cb9d1705"
MOBILE_PROJECT = "42f3a6a1-5a14-4968-abc6-bc39fd8c2769"
DATA_PROJECT = "21943bf1-c30b-4a40-900e-afe3c71c1910"

async def seed():
    async with AsyncSessionLocal() as db:
        today = date.today()

        # Departments
        depts = [
            Department(id=uuid.uuid4(), org_id=uuid.UUID(ORG_ID), name="Engineering"),
            Department(id=uuid.uuid4(), org_id=uuid.UUID(ORG_ID), name="Product"),
            Department(id=uuid.uuid4(), org_id=uuid.UUID(ORG_ID), name="Infrastructure"),
        ]
        for d in depts:
            db.add(d)

        # Contractors - API Platform v2 has schedule pressure, makes sense to add a contractor
        contractors = [
            ContractorCost(
                id=uuid.uuid4(), project_id=uuid.UUID(API_PROJECT),
                contractor_name="Alex Rivera", role="Backend Engineer", daily_rate=850,
                start_date=today - timedelta(days=5), end_date=None,
                reason_added="deadline_pressure", notes="Added to help with overdue tasks"
            ),
            ContractorCost(
                id=uuid.uuid4(), project_id=uuid.UUID(MOBILE_PROJECT),
                contractor_name="Jordan Lee", role="UI/UX Designer", daily_rate=650,
                start_date=today - timedelta(days=20), end_date=today - timedelta(days=5),
                reason_added="skill_gap", notes="Short-term design sprint support"
            ),
        ]
        for c in contractors:
            db.add(c)

        # Tool costs across projects
        tool_costs = [
            ToolCost(id=uuid.uuid4(), project_id=uuid.UUID(API_PROJECT), tool_name="AWS Aurora", monthly_cost=180, active_from=date(2026,1,1)),
            ToolCost(id=uuid.uuid4(), project_id=uuid.UUID(API_PROJECT), tool_name="Railway Hosting", monthly_cost=45, active_from=date(2026,1,1)),
            ToolCost(id=uuid.uuid4(), project_id=uuid.UUID(MOBILE_PROJECT), tool_name="Figma", monthly_cost=75, active_from=date(2026,2,1)),
            ToolCost(id=uuid.uuid4(), project_id=uuid.UUID(MOBILE_PROJECT), tool_name="TestFlight Distribution", monthly_cost=30, active_from=date(2026,2,1)),
            ToolCost(id=uuid.uuid4(), project_id=uuid.UUID(DATA_PROJECT), tool_name="Snowflake", monthly_cost=420, active_from=date(2026,3,1)),
        ]
        for t in tool_costs:
            db.add(t)

        await db.commit()
        print(f"Seeded {len(depts)} departments, {len(contractors)} contractors, {len(tool_costs)} tool costs")

asyncio.run(seed())

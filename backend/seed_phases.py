import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.project import Project
from app.models.project_phase import ProjectPhase
import uuid
from datetime import date
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

PHASE_TEMPLATES = {
    "sprint": [
        ("Discovery", 0.15, date(2026,1,1), date(2026,1,20)),
        ("Build", 0.55, date(2026,1,21), date(2026,5,15)),
        ("Testing & QA", 0.20, date(2026,5,16), date(2026,6,10)),
        ("Launch", 0.10, date(2026,6,11), date(2026,6,30)),
    ],
    "medium": [
        ("Discovery", 0.10, date(2026,2,1), date(2026,2,28)),
        ("Design", 0.20, date(2026,3,1), date(2026,4,15)),
        ("Build", 0.45, date(2026,4,16), date(2026,7,15)),
        ("QA & Polish", 0.15, date(2026,7,16), date(2026,8,15)),
        ("Launch", 0.10, date(2026,8,16), date(2026,8,31)),
    ],
    "program": [
        ("Discovery", 0.10, date(2026,3,1), date(2026,4,15)),
        ("Architecture", 0.15, date(2026,4,16), date(2026,6,15)),
        ("Build Phase 1", 0.25, date(2026,6,16), date(2026,9,15)),
        ("Build Phase 2", 0.25, date(2026,9,16), date(2026,11,15)),
        ("Integration & QA", 0.15, date(2026,11,16), date(2026,12,15)),
        ("Launch", 0.10, date(2026,12,16), date(2026,12,31)),
    ],
}

async def seed():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project))
        projects = result.scalars().all()

        for p in projects:
            template = PHASE_TEMPLATES.get(p.duration_type, PHASE_TEMPLATES["sprint"])
            today = date.today()
            for i, (name, pct, p_start, p_end) in enumerate(template):
                if p_end < today:
                    status = "completed"
                    actual_start, actual_end = p_start, p_end
                elif p_start <= today <= p_end:
                    status = "active"
                    actual_start, actual_end = p_start, None
                else:
                    status = "pending"
                    actual_start, actual_end = None, None

                phase = ProjectPhase(
                    id=uuid.uuid4(),
                    project_id=p.id,
                    name=name,
                    phase_order=i+1,
                    planned_start=p_start,
                    planned_end=p_end,
                    actual_start=actual_start,
                    actual_end=actual_end,
                    budget_allocation_pct=pct * 100,
                    status=status,
                )
                db.add(phase)

        await db.commit()
        print(f"Seeded phases for {len(projects)} projects")

asyncio.run(seed())

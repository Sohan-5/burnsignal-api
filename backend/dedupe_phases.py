import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from app.models.project_phase import ProjectPhase
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def dedupe():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ProjectPhase).order_by(ProjectPhase.created_at))
        all_phases = result.scalars().all()
        seen = set()
        to_delete = []
        for p in all_phases:
            key = (p.project_id, p.phase_order)
            if key in seen:
                to_delete.append(p.id)
            else:
                seen.add(key)
        for pid in to_delete:
            await db.execute(delete(ProjectPhase).where(ProjectPhase.id == pid))
        await db.commit()
        print(f"Deleted {len(to_delete)} duplicate phases")

asyncio.run(dedupe())

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.time_entry import TimeEntry
import uuid
from datetime import date, timedelta
import os
import random

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

PROJECTS = {
    "42f3a6a1-5a14-4968-abc6-bc39fd8c2769": {"days": 21, "min_h": 5, "max_h": 10, "rate": 150},   # Mobile Redesign - heavier burn
    "21943bf1-c30b-4a40-900e-afe3c71c1910": {"days": 18, "min_h": 3, "max_h": 6, "rate": 175},    # Data Pipeline - lighter burn
}

async def seed():
    async with AsyncSessionLocal() as db:
        today = date.today()
        total = 0
        for project_id, cfg in PROJECTS.items():
            for i in range(cfg["days"], 0, -1):
                d = today - timedelta(days=i)
                hours = round(random.uniform(cfg["min_h"], cfg["max_h"]), 1)
                te = TimeEntry(
                    id=uuid.uuid4(),
                    project_id=uuid.UUID(project_id),
                    hours=hours,
                    hourly_rate=cfg["rate"],
                    entry_date=d,
                    notes="seed data",
                    source="manual",
                )
                db.add(te)
                total += 1
        await db.commit()
        print(f"Seeded {total} time entries across 2 projects")

asyncio.run(seed())

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

PROJECT_ID = "5ee235b5-0d3c-4665-ab4f-a264cb9d1705"

async def seed():
    async with AsyncSessionLocal() as db:
        today = date.today()
        for i in range(14, 0, -1):
            d = today - timedelta(days=i)
            hours = round(random.uniform(4, 9), 1)
            rate = 150.0
            te = TimeEntry(
                id=uuid.uuid4(),
                project_id=uuid.UUID(PROJECT_ID),
                hours=hours,
                hourly_rate=rate,
                entry_date=d,
                notes="seed data",
                source="manual",
            )
            db.add(te)
        await db.commit()
        print("Seeded 14 days of time entries")

asyncio.run(seed())

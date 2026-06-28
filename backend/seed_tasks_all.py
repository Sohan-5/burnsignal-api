import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.tool_connection import ToolConnection
from app.models.imported_task import ImportedTask
import uuid
from datetime import date, timedelta, datetime, timezone
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

ORG_ID = "fb82c0b3-2153-4393-8169-8169ea907d73"

# Mobile Redesign - healthy project, on track
MOBILE_PROJECT = "42f3a6a1-5a14-4968-abc6-bc39fd8c2769"
MOBILE_TASKS = [
    ("Design system audit", "completed", -15, -12),
    ("Component library v2", "completed", -12, -8),
    ("Navigation redesign", "completed", -8, -5),
    ("Onboarding flow", "completed", -5, -2),
    ("Settings screen", "in_progress", 2, None),
    ("Profile redesign", "in_progress", 5, None),
    ("Dark mode support", "todo", 10, None),
    ("Accessibility pass", "todo", 14, None),
]

# Data Pipeline - early stage, minimal signal yet
DATA_PROJECT = "21943bf1-c30b-4a40-900e-afe3c71c1910"
DATA_TASKS = [
    ("Requirements gathering", "completed", -10, -8),
    ("Architecture review", "completed", -8, -5),
    ("Schema design", "in_progress", 5, None),
    ("ETL pipeline scaffold", "todo", 20, None),
]

async def get_or_create_connection(db, org_id):
    result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.org_id == uuid.UUID(org_id),
            ToolConnection.provider == "manual"
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    conn = ToolConnection(
        id=uuid.uuid4(), org_id=uuid.UUID(org_id),
        provider="manual", access_token="seed-placeholder-token", config={},
    )
    db.add(conn)
    await db.flush()
    return conn

async def seed_project_tasks(db, conn, project_id, task_list):
    today = date.today()
    for title, status, due_offset, completed_offset in task_list:
        due = today + timedelta(days=due_offset) if due_offset is not None else None
        completed = today + timedelta(days=completed_offset) if completed_offset is not None else None
        is_overdue = (due < today and status != "completed") if due else False
        t = ImportedTask(
            id=uuid.uuid4(),
            project_id=uuid.UUID(project_id),
            connection_id=conn.id,
            external_id=str(uuid.uuid4())[:8],
            title=title,
            status=status,
            due_date=due,
            completed_at=datetime.combine(completed, datetime.min.time(), tzinfo=timezone.utc) if completed else None,
            is_overdue=is_overdue,
        )
        db.add(t)

async def seed():
    async with AsyncSessionLocal() as db:
        conn = await get_or_create_connection(db, ORG_ID)
        await seed_project_tasks(db, conn, MOBILE_PROJECT, MOBILE_TASKS)
        await seed_project_tasks(db, conn, DATA_PROJECT, DATA_TASKS)
        await db.commit()
        print(f"Seeded tasks for Mobile Redesign ({len(MOBILE_TASKS)}) and Data Pipeline ({len(DATA_TASKS)})")

asyncio.run(seed())

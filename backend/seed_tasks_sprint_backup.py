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

# Mobile Redesign - already has some tasks, add a few more recent sprint tasks
MOBILE_PROJECT = "42f3a6a1-5a14-4968-abc6-bc39fd8c2769"
MOBILE_EXTRA = [
    ("API integration testing", "completed", -3, -1),
    ("Push notification setup", "in_progress", 4, None),
    ("Analytics dashboard", "todo", 8, None),
]

# Data Pipeline - early stage, add a realistic sprint of tasks
DATA_PROJECT = "21943bf1-c30b-4a40-900e-afe3c71c1910"
DATA_EXTRA = [
    ("Set up Airflow DAGs", "completed", -7, -5),
    ("Configure data validation rules", "completed", -5, -3),
    ("Build ingestion connectors", "in_progress", 3, None),
    ("Write transformation logic", "todo", 10, None),
    ("Set up monitoring alerts", "todo", 15, None),
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
        await seed_project_tasks(db, conn, MOBILE_PROJECT, MOBILE_EXTRA)
        await seed_project_tasks(db, conn, DATA_PROJECT, DATA_EXTRA)
        await db.commit()
        print(f"Seeded {len(MOBILE_EXTRA)} more Mobile tasks, {len(DATA_EXTRA)} Data Pipeline tasks")

asyncio.run(seed())

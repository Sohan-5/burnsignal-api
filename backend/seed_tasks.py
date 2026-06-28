import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.tool_connection import ToolConnection
from app.models.imported_task import ImportedTask
import uuid
from datetime import date, timedelta, datetime, timezone
import os

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

ORG_ID = "fb82c0b3-2153-4393-8169-8169ea907d73"
PROJECT_ID = "5ee235b5-0d3c-4665-ab4f-a264cb9d1705"

async def seed():
    async with AsyncSessionLocal() as db:
        conn = ToolConnection(
            id=uuid.uuid4(),
            org_id=uuid.UUID(ORG_ID),
            provider="manual",
            access_token="seed-placeholder-token",
            config={},
        )
        db.add(conn)
        await db.flush()

        today = date.today()
        tasks = [
            ("Implement auth middleware", "completed", today - timedelta(days=10), today - timedelta(days=8)),
            ("Build rate limiter", "completed", today - timedelta(days=8), today - timedelta(days=6)),
            ("Add request logging", "completed", today - timedelta(days=6), today - timedelta(days=4)),
            ("Write integration tests", "in_progress", today - timedelta(days=2), None),
            ("Fix pagination bug", "in_progress", today - timedelta(days=1), None),
            ("Update API docs", "todo", today + timedelta(days=3), None),
            ("Refactor error handling", "todo", today - timedelta(days=1), None),  # overdue
            ("Add webhook support", "todo", today - timedelta(days=3), None),  # overdue
        ]

        for title, status, due, completed in tasks:
            is_overdue = (due < today and status != "completed") if due else False
            t = ImportedTask(
                id=uuid.uuid4(),
                project_id=uuid.UUID(PROJECT_ID),
                connection_id=conn.id,
                external_id=str(uuid.uuid4())[:8],
                title=title,
                status=status,
                due_date=due,
                completed_at=datetime.combine(completed, datetime.min.time(), tzinfo=timezone.utc) if completed else None,
                is_overdue=is_overdue,
            )
            db.add(t)

        await db.commit()
        print(f"Seeded 1 tool connection + {len(tasks)} tasks")

asyncio.run(seed())

"""
Trello OAuth flow, board/card fetching, and full sync pipeline.
"""
import httpx
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.integrations.normalizer import normalize_trello_card

TRELLO_BASE = "https://api.trello.com/1"


def get_auth_url() -> str:
    """Returns Trello OAuth URL. User is redirected here to grant access."""
    return (
        f"https://trello.com/1/authorize"
        f"?expiration=never&scope=read&response_type=token"
        f"&name=BurnSignal&key={settings.TRELLO_API_KEY}"
        f"&return_url={settings.TRELLO_REDIRECT_URI}"
    )


async def get_boards(token: str) -> list[dict]:
    """Returns all Trello boards the user has access to."""
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{TRELLO_BASE}/members/me/boards",
            params={
                "key": settings.TRELLO_API_KEY,
                "token": token,
                "fields": "id,name,desc,url,closed",
                "filter": "open",
            }
        )
        res.raise_for_status()
        return res.json()


async def get_lists(board_id: str, token: str) -> list[dict]:
    """Returns all lists (columns) on a board — used for status mapping."""
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{TRELLO_BASE}/boards/{board_id}/lists",
            params={"key": settings.TRELLO_API_KEY, "token": token, "fields": "id,name"}
        )
        res.raise_for_status()
        return res.json()


async def get_cards(board_id: str, token: str) -> list[dict]:
    """Returns all open cards with custom fields (for story points)."""
    async with httpx.AsyncClient() as client:
        # Fetch cards
        cards_res = await client.get(
            f"{TRELLO_BASE}/boards/{board_id}/cards",
            params={
                "key": settings.TRELLO_API_KEY,
                "token": token,
                "fields": "id,name,due,dueComplete,dateLastActivity,idList,closed",
                "customFieldItems": "true",
                "filter": "open",
            }
        )
        cards_res.raise_for_status()
        cards = cards_res.json()

        # Fetch lists to get names for status mapping
        lists_res = await client.get(
            f"{TRELLO_BASE}/boards/{board_id}/lists",
            params={"key": settings.TRELLO_API_KEY, "token": token, "fields": "id,name"}
        )
        lists_res.raise_for_status()
        lists_map = {lst["id"]: lst["name"] for lst in lists_res.json()}

        # Enrich cards with list name
        for card in cards:
            card["list_name"] = lists_map.get(card.get("idList", ""), "")

        return cards


async def sync_board_to_project(
    db: AsyncSession,
    project_id: str,
    connection_id: str,
    board_id: str,
    token: str,
    hours_per_story_point: float = 2.0,
    status_mapping: dict = None,
) -> dict:
    """
    Full sync pipeline:
    1. Fetch all cards from Trello board
    2. Normalize to imported_tasks shape
    3. Upsert into DB (insert new, update changed, skip identical)
    4. Update connection.last_synced_at
    Returns sync result counts.
    """
    cards = await get_cards(board_id, token)

    created = 0
    updated = 0
    skipped = 0

    for card in cards:
        normalized = normalize_trello_card(
            card, project_id, connection_id, hours_per_story_point
        )

        # Apply custom status mapping if provided
        if status_mapping and normalized["status"] in status_mapping:
            normalized["status"] = status_mapping[normalized["status"]]

        # Check overdue
        if normalized.get("due_date"):
            due = date.fromisoformat(normalized["due_date"][:10]) if isinstance(normalized["due_date"], str) else normalized["due_date"]
            normalized["is_overdue"] = due < date.today() and normalized["status"] != "completed"

        # Upsert — insert or update based on external_id
        existing = await db.execute(text("""
            SELECT id, status, estimated_hours, is_overdue
            FROM imported_tasks
            WHERE project_id = :project_id
              AND connection_id = :connection_id
              AND external_id = :external_id
        """), {
            "project_id": project_id,
            "connection_id": connection_id,
            "external_id": normalized["external_id"],
        })
        row = existing.fetchone()

        if row is None:
            # Insert new task
            await db.execute(text("""
                INSERT INTO imported_tasks
                    (project_id, connection_id, external_id, title, status,
                     estimated_hours, actual_hours, due_date, completed_at, is_overdue, synced_at)
                VALUES
                    (:project_id, :connection_id, :external_id, :title, :status,
                     :estimated_hours, :actual_hours, :due_date, :completed_at, :is_overdue, NOW())
            """), normalized)
            created += 1

        elif (row.status != normalized["status"] or
              float(row.estimated_hours or 0) != float(normalized.get("estimated_hours") or 0) or
              row.is_overdue != normalized.get("is_overdue", False)):
            # Update only if something changed
            await db.execute(text("""
                UPDATE imported_tasks SET
                    title = :title,
                    status = :status,
                    estimated_hours = :estimated_hours,
                    actual_hours = :actual_hours,
                    due_date = :due_date,
                    completed_at = :completed_at,
                    is_overdue = :is_overdue,
                    synced_at = NOW()
                WHERE project_id = :project_id
                  AND connection_id = :connection_id
                  AND external_id = :external_id
            """), normalized)
            updated += 1
        else:
            skipped += 1

    # Update baseline task count on project if not set
    await db.execute(text("""
        UPDATE projects
        SET baseline_task_count = COALESCE(baseline_task_count, :count)
        WHERE id = :project_id AND baseline_task_count IS NULL
    """), {"project_id": project_id, "count": len(cards)})

    # Update last_synced_at on connection
    await db.execute(text("""
        UPDATE tool_connections SET last_synced_at = NOW() WHERE id = :connection_id
    """), {"connection_id": connection_id})

    await db.commit()

    # Trigger forecast invalidation after sync
    from app.forecast.forecast import invalidate_forecast
    await invalidate_forecast(project_id)

    return {
        "tasks_created": created,
        "tasks_updated": updated,
        "tasks_skipped": skipped,
        "synced_at": datetime.utcnow().isoformat(),
    }

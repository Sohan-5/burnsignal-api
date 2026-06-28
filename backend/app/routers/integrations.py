import os
import uuid
import httpx
from datetime import date, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from requests_oauthlib import OAuth1Session
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tool_connection import ToolConnection
from app.models.imported_task import ImportedTask
from app.models.project import Project
from app.forecast.forecast import run_forecast

router = APIRouter()

TRELLO_API_KEY = os.environ.get("TRELLO_API_KEY", "")
TRELLO_API_SECRET = os.environ.get("TRELLO_API_SECRET", "")
TRELLO_REQUEST_TOKEN_URL = "https://trello.com/1/OAuthGetRequestToken"
TRELLO_AUTHORIZE_URL = "https://trello.com/1/OAuthAuthorizeToken"
TRELLO_ACCESS_TOKEN_URL = "https://trello.com/1/OAuthGetAccessToken"
TRELLO_API_BASE = "https://api.trello.com/1"

BACKEND_CALLBACK = "https://burnsignal-api-production.up.railway.app/api/orgs/{org_id}/integrations/trello/callback"

# In-memory store for request-token secrets (ephemeral, fine for demo)
_request_token_secrets: dict[str, str] = {}


class SyncRequest(BaseModel):
    board_id: str
    project_id: str


def _trello_session(access_token: str, access_token_secret: str) -> OAuth1Session:
    return OAuth1Session(
        TRELLO_API_KEY,
        client_secret=TRELLO_API_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )


# ── Connect: redirect user to Trello authorise page ──────────────────────────

@router.get("/{org_id}/integrations/trello/connect")
async def trello_connect(org_id: str):
    if not TRELLO_API_KEY or not TRELLO_API_SECRET:
        raise HTTPException(status_code=500, detail="Trello API credentials not configured")

    callback_url = BACKEND_CALLBACK.format(org_id=org_id)
    oauth = OAuth1Session(
        TRELLO_API_KEY,
        client_secret=TRELLO_API_SECRET,
        callback_uri=callback_url,
    )
    fetch_response = oauth.fetch_request_token(TRELLO_REQUEST_TOKEN_URL)
    request_token = fetch_response.get("oauth_token")
    request_token_secret = fetch_response.get("oauth_token_secret")
    _request_token_secrets[request_token] = request_token_secret

    auth_url = (
        f"{TRELLO_AUTHORIZE_URL}"
        f"?oauth_token={request_token}"
        f"&name=BurnSignal"
        f"&expiration=never"
        f"&scope=read"
    )
    return RedirectResponse(url=auth_url)


# ── Callback: exchange verifier for access token, store in DB ────────────────

@router.get("/{org_id}/integrations/trello/callback")
async def trello_callback(
    org_id: str,
    oauth_token: str = Query(...),
    oauth_verifier: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    request_token_secret = _request_token_secrets.pop(oauth_token, None)
    if not request_token_secret:
        raise HTTPException(status_code=400, detail="OAuth session expired or invalid. Please reconnect.")

    oauth = OAuth1Session(
        TRELLO_API_KEY,
        client_secret=TRELLO_API_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=request_token_secret,
        verifier=oauth_verifier,
    )
    tokens = oauth.fetch_access_token(TRELLO_ACCESS_TOKEN_URL)
    access_token = tokens["oauth_token"]
    access_token_secret = tokens["oauth_token_secret"]

    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.org_id == org_uuid,
            ToolConnection.provider == "trello",
        )
    )
    connection = result.scalar_one_or_none()

    if connection:
        connection.access_token = access_token
        connection.refresh_token = access_token_secret
        connection.config = {}
    else:
        connection = ToolConnection(
            org_id=org_uuid,
            provider="trello",
            access_token=access_token,
            refresh_token=access_token_secret,
            config={},
        )
        db.add(connection)

    await db.commit()
    await db.refresh(connection)

    return RedirectResponse(
        url=f"https://burnsignal.vercel.app/integrations/trello/boards?connection_id={connection.id}"
    )


# ── Boards: list the user's open Trello boards ───────────────────────────────

@router.get("/{org_id}/integrations/trello/boards")
async def trello_boards(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.org_id == org_uuid,
            ToolConnection.provider == "trello",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="No Trello connection found. Connect first.")

    session = _trello_session(connection.access_token, connection.refresh_token)
    resp = session.get(
        f"{TRELLO_API_BASE}/members/me/boards",
        params={"fields": "id,name,url,closed", "filter": "open"},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Trello API error: {resp.text}")

    boards = [
        {"id": b["id"], "name": b["name"], "url": b["url"]}
        for b in resp.json()
        if not b.get("closed")
    ]
    return {"boards": boards, "connection_id": str(connection.id)}


# ── Sync: pull cards from a board into imported_tasks ────────────────────────

@router.post("/{org_id}/integrations/trello/sync")
async def trello_sync(
    org_id: str,
    body: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    org_uuid = uuid.UUID(org_id)
    project_uuid = uuid.UUID(body.project_id)

    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_uuid,
            Project.org_id == org_uuid,
        )
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this org.")

    conn_result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.org_id == org_uuid,
            ToolConnection.provider == "trello",
        )
    )
    connection = conn_result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="No Trello connection found. Connect first.")

    session = _trello_session(connection.access_token, connection.refresh_token)

    lists_resp = session.get(
        f"{TRELLO_API_BASE}/boards/{body.board_id}/lists",
        params={"fields": "id,name"},
    )
    if lists_resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Trello lists error: {lists_resp.text}")

    DONE_NAMES = {"done", "complete", "completed", "finished", "closed"}
    list_status: dict[str, str] = {}
    for lst in lists_resp.json():
        list_status[lst["id"]] = (
            "completed" if lst["name"].strip().lower() in DONE_NAMES else "todo"
        )

    cards_resp = session.get(
        f"{TRELLO_API_BASE}/boards/{body.board_id}/cards",
        params={"fields": "id,name,idList,due,dueComplete,dateLastActivity"},
    )
    if cards_resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Trello cards error: {cards_resp.text}")

    cards = cards_resp.json()
    now = date.today()

    await db.execute(
        delete(ImportedTask).where(
            ImportedTask.project_id == project_uuid,
            ImportedTask.connection_id == connection.id,
        )
    )

    synced_count = 0
    for card in cards:
        status = list_status.get(card["idList"], "todo")

        due_date: Optional[date] = None
        if card.get("due"):
            try:
                due_date = date.fromisoformat(card["due"][:10])
            except ValueError:
                pass

        is_overdue = (
            due_date is not None
            and due_date < now
            and status != "completed"
        )

        completed_at = None
        if status == "completed" and card.get("dateLastActivity"):
            try:
                from datetime import datetime
                completed_at = datetime.fromisoformat(
                    card["dateLastActivity"].replace("Z", "+00:00")
                )
            except ValueError:
                pass

        db.add(ImportedTask(
            project_id=project_uuid,
            connection_id=connection.id,
            external_id=card["id"],
            title=card["name"],
            status=status,
            due_date=due_date,
            is_overdue=is_overdue,
            completed_at=completed_at,
        ))
        synced_count += 1

    from datetime import datetime
    connection.last_synced_at = datetime.now(timezone.utc)
    connection.config = {**(connection.config or {}), "board_id": body.board_id}
    await db.commit()

    try:
        await run_forecast(str(project_uuid), db)
    except Exception:
        pass

    return {
        "synced": synced_count,
        "project_id": body.project_id,
        "board_id": body.board_id,
        "connection_id": str(connection.id),
    }


# ── Status: is this org connected to Trello? ─────────────────────────────────

@router.get("/{org_id}/integrations/trello/status")
async def trello_status(org_id: str, db: AsyncSession = Depends(get_db)):
    org_uuid = uuid.UUID(org_id)
    result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.org_id == org_uuid,
            ToolConnection.provider == "trello",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        return {"connected": False}

    return {
        "connected": True,
        "connection_id": str(connection.id),
        "last_synced_at": connection.last_synced_at.isoformat() if connection.last_synced_at else None,
        "board_id": connection.config.get("board_id") if connection.config else None,
    }


# ── Disconnect: delete connection + cascade imported_tasks ───────────────────

@router.delete("/{org_id}/integrations/trello/{connection_id}")
async def trello_disconnect(
    org_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
):
    org_uuid = uuid.UUID(org_id)
    conn_uuid = uuid.UUID(connection_id)

    result = await db.execute(
        select(ToolConnection).where(
            ToolConnection.id == conn_uuid,
            ToolConnection.org_id == org_uuid,
            ToolConnection.provider == "trello",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")

    await db.delete(connection)
    await db.commit()
    return {"deleted": True, "connection_id": connection_id}

# ── Dev/setup utility: delete all imported_tasks NOT from a given connection ──

@router.delete("/{org_id}/integrations/cleanup-seeded-tasks")
async def cleanup_seeded_tasks(
    org_id: str,
    keep_connection_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    org_uuid = uuid.UUID(org_id)
    keep_uuid = uuid.UUID(keep_connection_id)

    from sqlalchemy import text
    await db.execute(
        text("""
            DELETE FROM imported_tasks
            WHERE connection_id != :keep_id
            AND project_id IN (
                SELECT id FROM projects WHERE org_id = :org_id
            )
        """),
        {"keep_id": keep_uuid, "org_id": org_uuid}
    )
    await db.commit()
    return {"deleted": "all seeded tasks not from Trello connection", "kept_connection_id": keep_connection_id}

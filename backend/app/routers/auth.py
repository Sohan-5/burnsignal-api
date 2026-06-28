from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth_middleware import clerk_auth_guard
from app.models.user import User
from app.models.organization import Organization
from app.config import settings
from svix.webhooks import Webhook, WebhookVerificationError
import uuid

router = APIRouter()


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db), _=Depends(clerk_auth_guard)):
    auth_data = request.state.clerk_auth
    clerk_user_id = auth_data.decoded.get("sub")

    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()

    if not user:
        return {
            "synced": False,
            "clerk_user_id": clerk_user_id,
            "message": "User authenticated but not yet synced to database.",
        }

    return {
        "synced": True,
        "id": str(user.id),
        "org_id": str(user.org_id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }


async def _verify_webhook(request: Request) -> dict:
    payload = await request.body()
    headers = request.headers
    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        return wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


async def _handle_user_event(data: dict, db: AsyncSession):
    clerk_user_id = data.get("id")
    email_addresses = data.get("email_addresses", [])
    email = email_addresses[0]["email_address"] if email_addresses else f"{data.get('id', 'unknown')}@placeholder.clerk"
    first_name = data.get("first_name") or ""
    last_name = data.get("last_name") or ""
    name = f"{first_name} {last_name}".strip() or email or "Unknown"

    org_memberships = data.get("organization_memberships", [])
    clerk_org_id = org_memberships[0]["organization"]["id"] if org_memberships else None

    org_id = None
    if clerk_org_id:
        org_result = await db.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
        org = org_result.scalar_one_or_none()
        if org:
            org_id = org.id

    if not org_id:
        fallback = await db.execute(select(Organization).limit(1))
        fallback_org = fallback.scalar_one_or_none()
        org_id = fallback_org.id if fallback_org else None

    if not org_id:
        raise HTTPException(status_code=400, detail="No organization available")

    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()

    if user:
        user.email = email
        user.name = name
    else:
        user = User(
            id=uuid.uuid4(),
            org_id=org_id,
            clerk_user_id=clerk_user_id,
            email=email,
            name=name,
            role="member",
        )
        db.add(user)

    await db.commit()
    return {"status": "synced", "clerk_user_id": clerk_user_id}


async def _handle_org_event(data: dict, db: AsyncSession):
    clerk_org_id = data.get("id")
    name = data.get("name", "Unnamed Org")
    slug = data.get("slug") or clerk_org_id

    result = await db.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
    org = result.scalar_one_or_none()

    if org:
        org.name = name
    else:
        org = Organization(
            id=uuid.uuid4(),
            clerk_org_id=clerk_org_id,
            name=name,
            slug=slug,
            plan="free",
        )
        db.add(org)

    await db.commit()
    return {"status": "synced", "clerk_org_id": clerk_org_id}


@router.post("/sync-user")
async def webhook_handler(request: Request, db: AsyncSession = Depends(get_db)):
    event = await _verify_webhook(request)
    event_type = event.get("type")
    data = event.get("data", {})

    if event_type in ("user.created", "user.updated"):
        return await _handle_user_event(data, db)
    elif event_type in ("organization.created", "organization.updated"):
        return await _handle_org_event(data, db)
    else:
        return {"status": "ignored", "type": event_type}


@router.post("/sync-org")
async def sync_org_legacy(request: Request, db: AsyncSession = Depends(get_db)):
    event = await _verify_webhook(request)
    event_type = event.get("type")
    data = event.get("data", {})
    if event_type in ("organization.created", "organization.updated"):
        return await _handle_org_event(data, db)
    return {"status": "ignored", "type": event_type}

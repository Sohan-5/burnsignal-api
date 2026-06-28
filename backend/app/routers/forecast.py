from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.forecast.forecast import run_forecast
from app.forecast.store import get_latest, get_history, get_breach_date_drift
from dataclasses import asdict

router = APIRouter()

@router.post("/{org_id}/projects/{project_id}/forecast/run")
async def run_project_forecast(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await run_forecast(project_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    d = asdict(result)
    if d.get("predicted_breach_date"):
        d["predicted_breach_date"] = str(d["predicted_breach_date"])
    return d

@router.get("/{org_id}/projects/{project_id}/forecast/latest")
async def get_latest_forecast(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    snapshot = await get_latest(project_id, db)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No forecast snapshot yet — run /forecast/run first")
    return snapshot

@router.get("/{org_id}/projects/{project_id}/forecast/history")
async def get_forecast_history(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    return await get_history(project_id, db)

@router.get("/{org_id}/projects/{project_id}/forecast/breach-drift")
async def get_breach_drift(org_id: str, project_id: str, db: AsyncSession = Depends(get_db)):
    return await get_breach_date_drift(project_id, db)

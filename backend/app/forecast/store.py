"""
Persists forecast snapshots to Aurora PostgreSQL.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.forecast.combiner import ForecastResult
import json


async def save_snapshot(
    project_id: str,
    result: ForecastResult,
    burn_ratio: float,
    daily_burn_rate: float,
    data_points: int,
    db: AsyncSession,
) -> str:
    """Writes ForecastResult to forecast_snapshots. Returns snapshot id."""
    res = await db.execute(text("""
        INSERT INTO forecast_snapshots
            (project_id, tier, data_points, baseline_forecast, pressure_multiplier,
             final_forecast, predicted_breach_date, confidence_score,
             daily_burn_rate, burn_ratio, signal_values)
        VALUES
            (:project_id, :tier, :data_points, :baseline_forecast, :pressure_multiplier,
             :final_forecast, :predicted_breach_date, :confidence_score,
             :daily_burn_rate, :burn_ratio, :signal_values)
        RETURNING id
    """), {
        "project_id": project_id,
        "tier": result.tier,
        "data_points": data_points,
        "baseline_forecast": result.baseline_forecast,
        "pressure_multiplier": result.pressure_multiplier,
        "final_forecast": result.final_forecast,
        "predicted_breach_date": result.predicted_breach_date,
        "confidence_score": result.confidence_score,
        "daily_burn_rate": daily_burn_rate,
        "burn_ratio": burn_ratio,
        "signal_values": json.dumps(result.signal_values),
    })
    await db.commit()
    return str(res.scalar())


async def get_latest(project_id: str, db: AsyncSession) -> dict | None:
    """Returns most recent snapshot."""
    res = await db.execute(text("""
        SELECT * FROM forecast_snapshots
        WHERE project_id = :project_id
        ORDER BY snapshot_at DESC
        LIMIT 1
    """), {"project_id": project_id})
    row = res.fetchone()
    return dict(row._mapping) if row else None


async def get_history(project_id: str, db: AsyncSession, limit: int = 30) -> list[dict]:
    """Returns last N snapshots — powers breach date drift chart."""
    res = await db.execute(text("""
        SELECT id, snapshot_at, tier, predicted_breach_date,
               confidence_score, pressure_multiplier, burn_ratio, signal_values
        FROM forecast_snapshots
        WHERE project_id = :project_id
        ORDER BY snapshot_at DESC
        LIMIT :limit
    """), {"project_id": project_id, "limit": limit})
    return [dict(row._mapping) for row in res]


async def get_signal_trend(project_id: str, signal_name: str, db: AsyncSession) -> list[dict]:
    """Extracts one signal across all snapshots — shows how it changed over time."""
    res = await db.execute(text("""
        SELECT
            snapshot_at,
            (signal_values ->> :signal_name)::float AS value
        FROM forecast_snapshots
        WHERE project_id = :project_id
          AND signal_values ? :signal_name
        ORDER BY snapshot_at ASC
    """), {"project_id": project_id, "signal_name": signal_name})
    return [dict(row._mapping) for row in res]


async def get_breach_date_drift(project_id: str, db: AsyncSession) -> list[dict]:
    """
    Returns how predicted_breach_date changed over time.
    Powers the breach date drift chart — the most compelling demo visual.
    """
    res = await db.execute(text("""
        SELECT
            DATE(snapshot_at) AS snapshot_date,
            predicted_breach_date,
            confidence_score::float,
            tier
        FROM forecast_snapshots
        WHERE project_id = :project_id
          AND predicted_breach_date IS NOT NULL
        ORDER BY snapshot_at ASC
    """), {"project_id": project_id})
    return [dict(row._mapping) for row in res]

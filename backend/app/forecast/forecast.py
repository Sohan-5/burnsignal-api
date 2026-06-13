"""
Entry point for the ForecastService.
Called by:
  - POST /api/orgs/{org_id}/projects/{project_id}/forecast/run  (manual)
  - Daily cron job (app/jobs/cron.py)
  - invalidate_forecast() after any data mutation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.forecast.tier_selector import select_tier, get_signal_weights
from app.forecast.baseline import weighted_linear, holts_smoothing, holt_winters
from app.forecast.pressure import compute_all_signals
from app.forecast.calibration import load_priors
from app.forecast.combiner import combine, ForecastResult
from app.forecast.store import save_snapshot
from app.queries.burn import get_cumulative_spend_series, get_pressure_signals_data, get_daily_burn_rate, get_burn_summary
from app.jobs.queue import enqueue
from sqlalchemy import text


async def run_forecast(project_id: str, db: AsyncSession) -> ForecastResult:
    """
    Full forecast pipeline for one project.
    1. Load spend series + project state from DB
    2. Select tier based on data availability and duration_type
    3. Run baseline time series model
    4. Compute pressure signals
    5. Load calibration weights
    6. Combine into final forecast
    7. Save snapshot
    """
    # 1. Load data
    series = await get_cumulative_spend_series(db, project_id)
    data_points = len(series)
    burn_summary = await get_burn_summary(db, project_id)
    pressure_data = await get_pressure_signals_data(db, project_id)

    # Load project duration_type + historical count
    proj_result = await db.execute(text(
        "SELECT duration_type, org_id FROM projects WHERE id = :id"
    ), {"id": project_id})
    proj = proj_result.fetchone()
    if not proj:
        raise ValueError(f"Project {project_id} not found")

    hist_result = await db.execute(text(
        "SELECT COUNT(*) AS cnt FROM historical_projects WHERE org_id = :org_id AND source = 'org'"
    ), {"org_id": proj.org_id})
    historical_count = hist_result.scalar() or 0

    budget = float(burn_summary.get("total_budget", 0))
    if budget <= 0:
        raise ValueError(f"Project {project_id} has no budget set")

    # 2. Select tier
    tier_config = select_tier(proj.duration_type, data_points, historical_count)
    weights = get_signal_weights(tier_config)

    # 3. Baseline model
    baseline_result = {"tier": tier_config.tier, "data_points": data_points}
    if tier_config.tier == 1:
        baseline_result.update(weighted_linear(series, budget))
    elif tier_config.tier == "3b":
        baseline_result.update(holt_winters(series, budget))
    else:
        baseline_result.update(holts_smoothing(series, budget))

    # 4. Pressure signals
    signals = compute_all_signals(
        project=pressure_data["project"],
        tasks=pressure_data["tasks"],
        contractors=pressure_data["contractors"],
        snapshots=pressure_data["snapshots"],
        tier_config=tier_config,
    )

    # 5. Calibration weights
    hist_projects_result = await db.execute(text("""
        SELECT overrun_pct, signal_values_at_overrun, duration_type
        FROM historical_projects
        WHERE org_id = :org_id AND source = 'org'
        ORDER BY created_at DESC LIMIT 20
    """), {"org_id": proj.org_id})
    historical = [dict(r._mapping) for r in hist_projects_result]
    calibrated_weights = load_priors(str(proj.org_id), proj.duration_type, historical)

    # Merge tier weights with calibrated weights (calibrated takes precedence)
    final_weights = {**weights, **{k: v for k, v in calibrated_weights.get("signal_weights", {}).items() if k in signals}}

    # 6. Combine
    daily_burn = await get_daily_burn_rate(db, project_id)
    baseline_result["daily_burn_rate"] = daily_burn
    result = combine(baseline_result, signals, final_weights, budget)

    # Add burn ratio to snapshot
    burn_ratio = burn_summary.get("burn_ratio", 1.0)

    # 7. Save snapshot
    await save_snapshot(project_id, result, burn_ratio, daily_burn, data_points, db)

    return result


async def invalidate_forecast(project_id: str):
    """Called on any data mutation — queues a re-run."""
    enqueue(project_id)


async def schedule_forecast(org_id: str, db: AsyncSession):
    """Cron-triggered. Runs forecast for every active project in org."""
    result = await db.execute(text(
        "SELECT id FROM projects WHERE org_id = :org_id AND status = 'active'"
    ), {"org_id": org_id})
    for row in result:
        try:
            await run_forecast(str(row.id), db)
        except Exception as e:
            # Log and continue — one failing project shouldn't block others
            print(f"Forecast failed for project {row.id}: {e}")

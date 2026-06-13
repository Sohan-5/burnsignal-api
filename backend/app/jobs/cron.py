"""Daily forecast re-run for all active projects."""
from app.forecast.forecast import run_forecast

async def run_daily_forecasts(db):
    # TODO: query active projects and call run_forecast for each
    pass

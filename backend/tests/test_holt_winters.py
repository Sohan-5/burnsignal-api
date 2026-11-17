"""Tests for the Holt-Winters baseline (backend/app/forecast/baseline.py)."""
from datetime import date, timedelta
import itertools

from app.forecast.baseline import holt_winters, holts_smoothing


def _cumulative(daily):
    return list(itertools.accumulate(daily, initial=0.0))


def _seasonal_daily(days, base=1000.0, spike=3000.0, period=14):
    # spike on day 0 of every 14-day cycle (e.g. sprint-start invoices)
    return [base + (spike if d % period == 0 else 0.0) for d in range(days)]


def test_falls_back_to_holts_with_short_history():
    series = _cumulative([1000.0] * 20)  # < 2 cycles
    assert holt_winters(series, 100_000) == holts_smoothing(series, 100_000)


def test_returns_combiner_contract_keys():
    series = _cumulative(_seasonal_daily(56))
    out = holt_winters(series, 500_000)
    for key in ("breach_date", "level", "trend", "seasonal_factors", "confidence"):
        assert key in out
    assert out["level"] == series[-1]
    assert len(out["seasonal_factors"]) == 14


def test_learns_spike_position():
    series = _cumulative(_seasonal_daily(84))
    season = holt_winters(series, 1_000_000)["seasonal_factors"]
    assert season.index(max(season)) == 0
    assert max(season) > 1000  # spike clearly above the rest


def test_trend_is_deseasonalized_average_burn():
    series = _cumulative(_seasonal_daily(84))
    trend = holt_winters(series, 1_000_000)["trend"]
    expected = 1000 + 3000 / 14  # average daily burn ~ 1214
    assert abs(trend - expected) / expected < 0.15


def test_breach_date_roughly_correct():
    daily = _seasonal_daily(56)
    series = _cumulative(daily)
    avg = sum(daily) / len(daily)
    budget = series[-1] + avg * 30  # ~30 days of budget left
    breach = holt_winters(series, budget)["breach_date"]
    assert breach is not None
    assert abs((breach - date.today()).days - 30) <= 4


def test_already_over_budget_is_today():
    series = _cumulative(_seasonal_daily(56))
    assert holt_winters(series, series[-1] - 1)["breach_date"] == date.today()


def test_no_spend_means_no_breach():
    series = [5000.0] * 60
    out = holt_winters(series, 100_000)
    assert out["breach_date"] is None
    assert out["trend"] == 0.0


def test_long_program_horizon_still_finds_breach():
    # ~473 days of budget left; programs routinely run longer than a year
    daily = _seasonal_daily(63)
    series = _cumulative(daily)
    avg = sum(daily) / len(daily)
    budget = series[-1] + avg * 473
    breach = holt_winters(series, budget)["breach_date"]
    assert breach is not None
    assert abs((breach - date.today()).days - 473) <= 14


def test_weekday_only_calendar_series_projects_calendar_days():
    # $1000 per weekday, nothing on weekends, gap-filled to one point per day
    daily = [1000.0 if d % 7 < 5 else 0.0 for d in range(56)]
    series = _cumulative(daily)
    budget = series[-1] + 20_000  # 20 working days = 4 weeks starting Monday
    breach = holt_winters(series, budget)["breach_date"]
    assert (breach - date.today()).days == 26  # Friday of the 4th week


def test_output_works_with_combiner():
    from app.forecast.combiner import combine

    daily = _seasonal_daily(63)
    series = _cumulative(daily)
    budget = series[-1] + (sum(daily) / len(daily)) * 60
    hw = holt_winters(series, budget)
    baseline = {"tier": "3b", "data_points": len(series), **hw}

    no_pressure = combine(baseline, {}, {}, budget)
    assert no_pressure.tier == "3b"
    assert no_pressure.baseline_forecast == round(series[-1], 2)
    # combiner's linear date and the seasonal projection agree within a cycle
    assert abs((no_pressure.predicted_breach_date - hw["breach_date"]).days) <= 14

    pressured = combine(baseline, {"budget_acceleration": 1.0}, {"budget_acceleration": 0.5}, budget)
    assert pressured.pressure_multiplier == 1.5
    assert pressured.predicted_breach_date < no_pressure.predicted_breach_date


def test_negative_corrections_do_not_crash():
    daily = _seasonal_daily(56)
    daily[30] = -2000.0  # refund / correction entry
    out = holt_winters(_cumulative(daily), 500_000)
    assert out["trend"] >= 0

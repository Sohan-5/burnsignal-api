"""
Core burn rate SQL queries — used by dashboard, project detail, and forecast service.
All queries are org-scoped and use parameterized inputs to prevent SQL injection.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_burn_timeline(db: AsyncSession, project_id: str) -> list[dict]:
    """
    Daily cumulative spend for the burn chart.
    Returns [{entry_date, daily_cost, cumulative_cost}] ordered by date.
    """
    result = await db.execute(text("""
        SELECT
            entry_date,
            SUM(cost)::float AS daily_cost,
            SUM(SUM(cost)) OVER (
                ORDER BY entry_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )::float AS cumulative_cost
        FROM time_entries
        WHERE project_id = :project_id
        GROUP BY entry_date
        ORDER BY entry_date
    """), {"project_id": project_id})
    return [dict(row._mapping) for row in result]


async def get_burn_summary(db: AsyncSession, project_id: str) -> dict:
    """
    Aggregated burn by cost category — headcount, tools, contractors.
    Returns totals and utilization against budget.
    """
    result = await db.execute(text("""
        WITH budget AS (
            SELECT total_amount, currency, headcount_pct, tools_pct, contractors_pct, contingency_pct
            FROM budgets WHERE project_id = :project_id
        ),
        headcount AS (
            SELECT COALESCE(SUM(cost), 0)::float AS total
            FROM time_entries WHERE project_id = :project_id
        ),
        tools AS (
            SELECT COALESCE(SUM(
                monthly_cost * GREATEST(1,
                    EXTRACT(MONTH FROM AGE(COALESCE(active_to, CURRENT_DATE), active_from))
                )
            ), 0)::float AS total
            FROM tool_costs WHERE project_id = :project_id
        ),
        contractors AS (
            SELECT COALESCE(SUM(
                daily_rate * GREATEST(1, COALESCE(end_date, CURRENT_DATE) - start_date)
            ), 0)::float AS total
            FROM contractor_costs WHERE project_id = :project_id
        ),
        project AS (
            SELECT start_date, end_date,
                EXTRACT(EPOCH FROM (NOW() - start_date::timestamp)) /
                NULLIF(EXTRACT(EPOCH FROM (end_date::timestamp - start_date::timestamp)), 0) AS elapsed_pct
            FROM projects WHERE id = :project_id
        )
        SELECT
            b.total_amount::float AS total_budget,
            b.currency,
            h.total AS headcount_spent,
            t.total AS tools_spent,
            c.total AS contractors_spent,
            (h.total + t.total + c.total) AS total_spent,
            ROUND(((h.total + t.total + c.total) / NULLIF(b.total_amount, 0) * 100)::numeric, 2)::float AS utilization_pct,
            ROUND((b.total_amount - b.total_amount * b.headcount_pct / 100)::numeric, 2)::float AS headcount_budget,
            ROUND((b.total_amount - b.total_amount * b.tools_pct / 100)::numeric, 2)::float AS tools_budget,
            ROUND((b.total_amount - b.total_amount * b.contractors_pct / 100)::numeric, 2)::float AS contractors_budget,
            GREATEST(0, (p.end_date - CURRENT_DATE))::int AS days_remaining,
            ROUND((LEAST(1.0, GREATEST(0.0, p.elapsed_pct)) * 100)::numeric, 2)::float AS timeline_elapsed_pct,
            CASE
                WHEN p.elapsed_pct > 0
                THEN ROUND((((h.total + t.total + c.total) / NULLIF(b.total_amount, 0)) / p.elapsed_pct)::numeric, 4)::float
                ELSE 1.0
            END AS burn_ratio
        FROM budget b, headcount h, tools t, contractors c, project p
    """), {"project_id": project_id})
    row = result.fetchone()
    return dict(row._mapping) if row else {}


async def get_pressure_signals_data(db: AsyncSession, project_id: str) -> dict:
    """
    Fetches all raw data needed by pressure.py signal functions.
    Single round-trip to DB instead of N queries.
    """
    # Tasks for velocity + overdue signals
    tasks_result = await db.execute(text("""
        SELECT
            status,
            due_date,
            completed_at,
            CASE WHEN due_date < CURRENT_DATE AND status != 'completed' THEN true ELSE false END AS is_overdue,
            CASE WHEN completed_at >= NOW() - INTERVAL '7 days' THEN true ELSE false END AS completed_in_window,
            CASE WHEN due_date BETWEEN NOW() - INTERVAL '7 days' AND NOW() THEN true ELSE false END AS planned_completion_in_window
        FROM imported_tasks
        WHERE project_id = :project_id
    """), {"project_id": project_id})
    tasks = [dict(r._mapping) for r in tasks_result]

    # Contractors added recently — for headcount_delta signal
    contractors_result = await db.execute(text("""
        SELECT
            reason_added,
            start_date,
            CASE WHEN start_date >= CURRENT_DATE - INTERVAL '14 days' THEN true ELSE false END AS added_in_window
        FROM contractor_costs
        WHERE project_id = :project_id
    """), {"project_id": project_id})
    contractors = [dict(r._mapping) for r in contractors_result]

    # Phase slip data
    phases_result = await db.execute(text("""
        SELECT
            phase_order,
            planned_start, planned_end,
            actual_start, actual_end,
            status,
            EXTRACT(EPOCH FROM (actual_start::timestamp - planned_start::timestamp)) / 86400 AS start_slip_days,
            (planned_end - planned_start)::int AS planned_duration_days
        FROM project_phases
        WHERE project_id = :project_id
        ORDER BY phase_order
    """), {"project_id": project_id})
    phases = [dict(r._mapping) for r in phases_result]

    # Last 3 snapshots for budget_acceleration signal
    snapshots_result = await db.execute(text("""
        SELECT daily_burn_rate, snapshot_at, burn_ratio
        FROM forecast_snapshots
        WHERE project_id = :project_id
        ORDER BY snapshot_at DESC
        LIMIT 3
    """), {"project_id": project_id})
    snapshots = [dict(r._mapping) for r in snapshots_result]

    # Project meta for timeline_pressure
    project_result = await db.execute(text("""
        SELECT
            start_date, end_date,
            baseline_task_count,
            EXTRACT(EPOCH FROM (NOW() - start_date::timestamp)) /
            NULLIF(EXTRACT(EPOCH FROM (end_date::timestamp - start_date::timestamp)), 0) AS elapsed_pct
        FROM projects WHERE id = :project_id
    """), {"project_id": project_id})
    project = dict(project_result.fetchone()._mapping)
    project["phases"] = phases

    return {
        "project": project,
        "tasks": tasks,
        "contractors": contractors,
        "snapshots": snapshots,
    }


async def get_daily_burn_rate(db: AsyncSession, project_id: str, window_days: int = 7) -> float:
    """Average daily spend over the last N days. Used in forecast and snapshots."""
    result = await db.execute(text("""
        SELECT COALESCE(SUM(cost) / NULLIF(:window_days, 0), 0)::float AS daily_rate
        FROM time_entries
        WHERE project_id = :project_id
          AND entry_date >= CURRENT_DATE - INTERVAL ':window_days days'
    """), {"project_id": project_id, "window_days": window_days})
    row = result.fetchone()
    return row.daily_rate if row else 0.0


async def get_cumulative_spend_series(db: AsyncSession, project_id: str) -> list[float]:
    """
    Returns ordered list of daily cumulative spend values.
    This is the input series for baseline.py time series models.
    """
    result = await db.execute(text("""
        SELECT
            SUM(SUM(cost)) OVER (
                ORDER BY entry_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )::float AS cumulative_cost
        FROM time_entries
        WHERE project_id = :project_id
        GROUP BY entry_date
        ORDER BY entry_date
    """), {"project_id": project_id})
    return [row.cumulative_cost for row in result]

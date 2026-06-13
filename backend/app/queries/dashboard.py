"""
Dashboard aggregation queries — one per role view.
Each query returns everything the frontend needs in a single DB round-trip.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_eng_lead_dashboard(db: AsyncSession, org_id: str) -> dict:
    """
    All active projects with burn summary and latest forecast.
    Joined in one query to avoid N+1.
    """
    result = await db.execute(text("""
        SELECT
            p.id AS project_id,
            p.name,
            p.status,
            p.duration_type,
            p.start_date,
            p.end_date,
            GREATEST(0, (p.end_date - CURRENT_DATE))::int AS days_remaining,
            b.total_amount::float AS budget,
            b.currency,
            COALESCE(te.total_cost, 0)::float + COALESCE(tc.total_tool_cost, 0)::float + COALESCE(cc.total_contractor_cost, 0)::float AS total_spent,
            ROUND(
                (COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0))
                / NULLIF(b.total_amount, 0) * 100, 2
            )::float AS utilization_pct,
            fs.tier,
            fs.predicted_breach_date,
            fs.confidence_score::float,
            fs.pressure_multiplier::float,
            fs.burn_ratio::float,
            fs.signal_values
        FROM projects p
        LEFT JOIN budgets b ON b.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(cost) AS total_cost FROM time_entries GROUP BY project_id
        ) te ON te.project_id = p.id
        LEFT JOIN (
            SELECT project_id,
                SUM(monthly_cost * GREATEST(1, EXTRACT(MONTH FROM AGE(COALESCE(active_to, CURRENT_DATE), active_from)))) AS total_tool_cost
            FROM tool_costs GROUP BY project_id
        ) tc ON tc.project_id = p.id
        LEFT JOIN (
            SELECT project_id,
                SUM(daily_rate * GREATEST(1, COALESCE(end_date, CURRENT_DATE) - start_date)) AS total_contractor_cost
            FROM contractor_costs GROUP BY project_id
        ) cc ON cc.project_id = p.id
        LEFT JOIN LATERAL (
            SELECT tier, predicted_breach_date, confidence_score, pressure_multiplier, burn_ratio, signal_values
            FROM forecast_snapshots
            WHERE project_id = p.id
            ORDER BY snapshot_at DESC
            LIMIT 1
        ) fs ON true
        WHERE p.org_id = :org_id AND p.status = 'active'
        ORDER BY fs.burn_ratio DESC NULLS LAST, p.end_date ASC
    """), {"org_id": org_id})

    projects = [dict(row._mapping) for row in result]

    totals_result = await db.execute(text("""
        SELECT
            COALESCE(SUM(b.total_amount), 0)::float AS total_budget,
            COUNT(CASE WHEN fs.burn_ratio > 1.2 THEN 1 END) AS projects_at_risk,
            COUNT(CASE WHEN fs.burn_ratio > 1.5 THEN 1 END) AS projects_critical,
            ROUND(AVG(fs.confidence_score)::numeric, 3)::float AS avg_confidence
        FROM projects p
        LEFT JOIN budgets b ON b.project_id = p.id
        LEFT JOIN LATERAL (
            SELECT burn_ratio, confidence_score
            FROM forecast_snapshots WHERE project_id = p.id
            ORDER BY snapshot_at DESC LIMIT 1
        ) fs ON true
        WHERE p.org_id = :org_id AND p.status = 'active'
    """), {"org_id": org_id})
    totals = dict(totals_result.fetchone()._mapping)

    return {"projects": projects, **totals}


async def get_pm_dashboard(db: AsyncSession, org_id: str) -> dict:
    """Sprint velocity, task completion rates, cost per sprint."""
    result = await db.execute(text("""
        SELECT
            p.id AS project_id,
            p.name,
            p.duration_type,
            p.end_date,
            GREATEST(0, (p.end_date - CURRENT_DATE))::int AS days_remaining,
            COALESCE(task_stats.total_tasks, 0)::int AS total_tasks,
            COALESCE(task_stats.completed_tasks, 0)::int AS completed_tasks,
            COALESCE(task_stats.overdue_tasks, 0)::int AS overdue_tasks,
            ROUND(COALESCE(task_stats.completion_rate, 0)::numeric, 1)::float AS completion_rate_pct,
            COALESCE(week_cost.cost_this_week, 0)::float AS cost_this_week,
            fs.burn_ratio::float,
            fs.predicted_breach_date
        FROM projects p
        LEFT JOIN (
            SELECT
                project_id,
                COUNT(*) AS total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed_tasks,
                COUNT(*) FILTER (WHERE is_overdue = true) AS overdue_tasks,
                ROUND(COUNT(*) FILTER (WHERE status = 'completed')::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS completion_rate
            FROM imported_tasks GROUP BY project_id
        ) task_stats ON task_stats.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(cost) AS cost_this_week
            FROM time_entries
            WHERE entry_date >= DATE_TRUNC('week', CURRENT_DATE)
            GROUP BY project_id
        ) week_cost ON week_cost.project_id = p.id
        LEFT JOIN LATERAL (
            SELECT burn_ratio, predicted_breach_date
            FROM forecast_snapshots WHERE project_id = p.id
            ORDER BY snapshot_at DESC LIMIT 1
        ) fs ON true
        WHERE p.org_id = :org_id AND p.status = 'active'
        ORDER BY task_stats.overdue_tasks DESC NULLS LAST
    """), {"org_id": org_id})

    projects = [dict(row._mapping) for row in result]

    summary = await db.execute(text("""
        SELECT
            COALESCE(SUM(it.total_tasks), 0)::int AS total_tasks,
            COALESCE(SUM(it.completed_tasks), 0)::int AS completed_tasks,
            COALESCE(SUM(it.overdue_tasks), 0)::int AS overdue_tasks,
            ROUND(AVG(it.completion_rate)::numeric, 1)::float AS avg_velocity_pct,
            COALESCE(SUM(wc.cost_this_week), 0)::float AS sprint_cost_this_week
        FROM projects p
        LEFT JOIN (
            SELECT project_id,
                COUNT(*) AS total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed_tasks,
                COUNT(*) FILTER (WHERE is_overdue = true) AS overdue_tasks,
                ROUND(COUNT(*) FILTER (WHERE status = 'completed')::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS completion_rate
            FROM imported_tasks GROUP BY project_id
        ) it ON it.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(cost) AS cost_this_week
            FROM time_entries WHERE entry_date >= DATE_TRUNC('week', CURRENT_DATE)
            GROUP BY project_id
        ) wc ON wc.project_id = p.id
        WHERE p.org_id = :org_id AND p.status = 'active'
    """), {"org_id": org_id})

    return {"projects": projects, **dict(summary.fetchone()._mapping)}


async def get_finance_dashboard(db: AsyncSession, org_id: str) -> dict:
    """Budget vs actuals across all departments, overrun flags, MoM spend."""
    by_dept = await db.execute(text("""
        SELECT
            d.id AS dept_id,
            d.name AS dept_name,
            COUNT(p.id)::int AS project_count,
            COALESCE(SUM(b.total_amount), 0)::float AS total_budget,
            COALESCE(SUM(
                COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0)
            ), 0)::float AS total_spent,
            ROUND(COALESCE(SUM(
                COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0)
            ) / NULLIF(SUM(b.total_amount), 0) * 100, 0)::numeric, 2)::float AS utilization_pct
        FROM departments d
        LEFT JOIN projects p ON p.department_id = d.id AND p.status = 'active'
        LEFT JOIN budgets b ON b.project_id = p.id
        LEFT JOIN (SELECT project_id, SUM(cost) AS total_cost FROM time_entries GROUP BY project_id) te ON te.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(monthly_cost * GREATEST(1, EXTRACT(MONTH FROM AGE(COALESCE(active_to, CURRENT_DATE), active_from)))) AS total_tool_cost
            FROM tool_costs GROUP BY project_id
        ) tc ON tc.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(daily_rate * GREATEST(1, COALESCE(end_date, CURRENT_DATE) - start_date)) AS total_contractor_cost
            FROM contractor_costs GROUP BY project_id
        ) cc ON cc.project_id = p.id
        WHERE d.org_id = :org_id
        GROUP BY d.id, d.name
        ORDER BY total_spent DESC
    """), {"org_id": org_id})

    mom_spend = await db.execute(text("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', entry_date), 'YYYY-MM') AS month,
            SUM(cost)::float AS spend
        FROM time_entries te
        JOIN projects p ON p.id = te.project_id
        WHERE p.org_id = :org_id
          AND entry_date >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY DATE_TRUNC('month', entry_date)
        ORDER BY month
    """), {"org_id": org_id})

    overrun_flags = await db.execute(text("""
        SELECT p.id AS project_id, p.name, fs.burn_ratio::float, fs.predicted_breach_date, fs.confidence_score::float
        FROM projects p
        JOIN LATERAL (
            SELECT burn_ratio, predicted_breach_date, confidence_score
            FROM forecast_snapshots WHERE project_id = p.id
            ORDER BY snapshot_at DESC LIMIT 1
        ) fs ON true
        WHERE p.org_id = :org_id AND p.status = 'active' AND fs.burn_ratio > 1.3
        ORDER BY fs.burn_ratio DESC
    """), {"org_id": org_id})

    totals = await db.execute(text("""
        SELECT
            COALESCE(SUM(b.total_amount), 0)::float AS total_budget_all,
            COALESCE(SUM(
                COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0)
            ), 0)::float AS total_spent_all
        FROM projects p
        LEFT JOIN budgets b ON b.project_id = p.id
        LEFT JOIN (SELECT project_id, SUM(cost) AS total_cost FROM time_entries GROUP BY project_id) te ON te.project_id = p.id
        LEFT JOIN (SELECT project_id, SUM(monthly_cost) AS total_tool_cost FROM tool_costs GROUP BY project_id) tc ON tc.project_id = p.id
        LEFT JOIN (SELECT project_id, SUM(daily_rate) AS total_contractor_cost FROM contractor_costs GROUP BY project_id) cc ON cc.project_id = p.id
        WHERE p.org_id = :org_id AND p.status = 'active'
    """), {"org_id": org_id})

    return {
        **dict(totals.fetchone()._mapping),
        "by_department": [dict(r._mapping) for r in by_dept],
        "mom_spend": [dict(r._mapping) for r in mom_spend],
        "overrun_flags": [dict(r._mapping) for r in overrun_flags],
    }


async def get_member_dashboard(db: AsyncSession, org_id: str, user_id: str) -> dict:
    """Personal view — my hours, my projects, recent entries."""
    hours = await db.execute(text("""
        SELECT
            COALESCE(SUM(hours) FILTER (WHERE entry_date >= DATE_TRUNC('week', CURRENT_DATE)), 0)::float AS hours_this_week,
            COALESCE(SUM(hours) FILTER (WHERE entry_date >= DATE_TRUNC('month', CURRENT_DATE)), 0)::float AS hours_this_month
        FROM time_entries
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    my_projects = await db.execute(text("""
        SELECT DISTINCT ON (p.id)
            p.id AS project_id, p.name, p.status, p.end_date,
            GREATEST(0, (p.end_date - CURRENT_DATE))::int AS days_remaining
        FROM projects p
        JOIN time_entries te ON te.project_id = p.id AND te.user_id = :user_id
        WHERE p.org_id = :org_id AND p.status = 'active'
        ORDER BY p.id, p.end_date ASC
    """), {"user_id": user_id, "org_id": org_id})

    recent = await db.execute(text("""
        SELECT te.id, te.entry_date, te.hours, te.cost::float, te.source, te.notes, p.name AS project_name
        FROM time_entries te
        JOIN projects p ON p.id = te.project_id
        WHERE te.user_id = :user_id
        ORDER BY te.entry_date DESC, te.created_at DESC
        LIMIT 10
    """), {"user_id": user_id})

    return {
        **dict(hours.fetchone()._mapping),
        "my_projects": [dict(r._mapping) for r in my_projects],
        "recent_entries": [dict(r._mapping) for r in recent],
    }

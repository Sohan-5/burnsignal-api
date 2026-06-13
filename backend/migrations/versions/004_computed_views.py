"""Analytical views for dashboard queries

Revision ID: 004
Revises: 003
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Daily cumulative burn per project — used for burn timeline chart
    op.execute("""
        CREATE OR REPLACE VIEW v_daily_burn AS
        SELECT
            project_id,
            entry_date,
            SUM(cost) AS daily_cost,
            SUM(SUM(cost)) OVER (
                PARTITION BY project_id
                ORDER BY entry_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS cumulative_cost
        FROM time_entries
        GROUP BY project_id, entry_date
    """)

    # Budget utilization per project — used for burn summary card
    op.execute("""
        CREATE OR REPLACE VIEW v_budget_utilization AS
        SELECT
            p.id AS project_id,
            p.org_id,
            p.name,
            p.status,
            p.duration_type,
            p.start_date,
            p.end_date,
            b.total_amount AS budget,
            b.currency,
            COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0) AS total_spent,
            CASE
                WHEN b.total_amount > 0
                THEN ROUND(
                    (COALESCE(te.total_cost, 0) + COALESCE(tc.total_tool_cost, 0) + COALESCE(cc.total_contractor_cost, 0))
                    / b.total_amount * 100, 2)
                ELSE 0
            END AS utilization_pct,
            CASE
                WHEN (p.end_date - p.start_date) > 0
                THEN ROUND(
                    EXTRACT(EPOCH FROM (NOW() - p.start_date::timestamp)) /
                    EXTRACT(EPOCH FROM (p.end_date::timestamp - p.start_date::timestamp)) * 100,
                    2)
                ELSE 0
            END AS timeline_elapsed_pct
        FROM projects p
        LEFT JOIN budgets b ON b.project_id = p.id
        LEFT JOIN (
            SELECT project_id, SUM(cost) AS total_cost FROM time_entries GROUP BY project_id
        ) te ON te.project_id = p.id
        LEFT JOIN (
            SELECT project_id,
                   SUM(monthly_cost * GREATEST(1, EXTRACT(MONTH FROM AGE(COALESCE(active_to, NOW()::date), active_from)))) AS total_tool_cost
            FROM tool_costs GROUP BY project_id
        ) tc ON tc.project_id = p.id
        LEFT JOIN (
            SELECT project_id,
                   SUM(daily_rate * GREATEST(1, COALESCE(end_date, NOW()::date) - start_date)) AS total_contractor_cost
            FROM contractor_costs GROUP BY project_id
        ) cc ON cc.project_id = p.id
    """)

    # Burn ratio signal — key health indicator used by pressure.py
    op.execute("""
        CREATE OR REPLACE VIEW v_burn_ratio AS
        SELECT
            project_id,
            total_spent,
            budget,
            utilization_pct / NULLIF(timeline_elapsed_pct, 0) AS burn_ratio
        FROM v_budget_utilization
    """)

    # Weekly velocity — tasks completed vs expected per project per week
    op.execute("""
        CREATE OR REPLACE VIEW v_weekly_velocity AS
        SELECT
            project_id,
            DATE_TRUNC('week', completed_at) AS week,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
            COUNT(*) AS total_count,
            ROUND(COUNT(*) FILTER (WHERE status = 'completed')::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS completion_rate_pct
        FROM imported_tasks
        WHERE completed_at IS NOT NULL OR due_date IS NOT NULL
        GROUP BY project_id, DATE_TRUNC('week', completed_at)
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_weekly_velocity")
    op.execute("DROP VIEW IF EXISTS v_burn_ratio")
    op.execute("DROP VIEW IF EXISTS v_budget_utilization")
    op.execute("DROP VIEW IF EXISTS v_daily_burn")

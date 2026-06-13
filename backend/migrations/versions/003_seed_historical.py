"""Seed historical_projects with ISBSG/NASA prior data for Tier 3B calibration

Revision ID: 003
Revises: 002
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json
from pathlib import Path

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Preprocessed from ISBSG research extract + NASA PROMISE repository
# Each record represents a historical project archetype used as a prior
SEED_RECORDS = [
    # ── Sprint projects ─────────────────────────────────────
    {"source": "isbsg", "duration_type": "sprint", "project_type": "web_feature",
     "planned_budget": 20000, "actual_budget": 23600, "overrun_pct": 0.18,
     "team_size": 3, "duration_days": 14,
     "phase_cost_breakdown": {"1_of_1": 1.0},
     "signal_values_at_overrun": {"velocity_gap": 0.42, "overdue_ratio": 0.38, "scope_creep_rate": 0.21}},

    {"source": "isbsg", "duration_type": "sprint", "project_type": "api_integration",
     "planned_budget": 15000, "actual_budget": 16800, "overrun_pct": 0.12,
     "team_size": 2, "duration_days": 14,
     "phase_cost_breakdown": {"1_of_1": 1.0},
     "signal_values_at_overrun": {"velocity_gap": 0.28, "overdue_ratio": 0.22, "headcount_delta": 0.0}},

    {"source": "nasa", "duration_type": "sprint", "project_type": "bug_fix_cycle",
     "planned_budget": 8000, "actual_budget": 9760, "overrun_pct": 0.22,
     "team_size": 2, "duration_days": 10,
     "phase_cost_breakdown": {"1_of_1": 1.0},
     "signal_values_at_overrun": {"velocity_gap": 0.55, "overdue_ratio": 0.45, "scope_creep_rate": 0.30}},

    # ── Medium projects ──────────────────────────────────────
    {"source": "isbsg", "duration_type": "medium", "project_type": "saas_feature_set",
     "planned_budget": 150000, "actual_budget": 190500, "overrun_pct": 0.27,
     "team_size": 6, "duration_days": 90,
     "phase_cost_breakdown": {"1_of_3": 0.24, "2_of_3": 0.54, "3_of_3": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.31, "velocity_gap": 0.38, "headcount_delta": 0.45}},

    {"source": "isbsg", "duration_type": "medium", "project_type": "mobile_app",
     "planned_budget": 200000, "actual_budget": 246000, "overrun_pct": 0.23,
     "team_size": 5, "duration_days": 120,
     "phase_cost_breakdown": {"1_of_3": 0.27, "2_of_3": 0.58, "3_of_3": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.25, "timeline_pressure": 0.72, "headcount_delta": 0.33}},

    {"source": "nasa", "duration_type": "medium", "project_type": "data_pipeline",
     "planned_budget": 80000, "actual_budget": 113600, "overrun_pct": 0.42,
     "team_size": 4, "duration_days": 60,
     "phase_cost_breakdown": {"1_of_2": 0.38, "2_of_2": 1.0},
     "signal_values_at_overrun": {"scope_creep_rate": 0.62, "velocity_gap": 0.48, "phase_slip_days": 0.41}},

    {"source": "isbsg", "duration_type": "medium", "project_type": "platform_migration",
     "planned_budget": 300000, "actual_budget": 390000, "overrun_pct": 0.30,
     "team_size": 8, "duration_days": 150,
     "phase_cost_breakdown": {"1_of_4": 0.18, "2_of_4": 0.40, "3_of_4": 0.70, "4_of_4": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.44, "headcount_delta": 0.67, "timeline_pressure": 0.85}},

    # ── Program / long-running ───────────────────────────────
    {"source": "isbsg", "duration_type": "program", "project_type": "erp_implementation",
     "planned_budget": 2000000, "actual_budget": 2900000, "overrun_pct": 0.45,
     "team_size": 20, "duration_days": 540,
     "phase_cost_breakdown": {"1_of_4": 0.14, "2_of_4": 0.36, "3_of_4": 0.67, "4_of_4": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.58, "budget_acceleration": 0.71, "headcount_delta": 0.80}},

    {"source": "isbsg", "duration_type": "program", "project_type": "platform_rebuild",
     "planned_budget": 1200000, "actual_budget": 1620000, "overrun_pct": 0.35,
     "team_size": 15, "duration_days": 365,
     "phase_cost_breakdown": {"1_of_3": 0.22, "2_of_3": 0.52, "3_of_3": 1.0},
     "signal_values_at_overrun": {"budget_acceleration": 0.62, "phase_slip_days": 0.45, "timeline_pressure": 0.77}},

    {"source": "nasa", "duration_type": "program", "project_type": "infrastructure_overhaul",
     "planned_budget": 800000, "actual_budget": 1248000, "overrun_pct": 0.56,
     "team_size": 12, "duration_days": 480,
     "phase_cost_breakdown": {"1_of_4": 0.16, "2_of_4": 0.39, "3_of_4": 0.71, "4_of_4": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.68, "budget_acceleration": 0.83, "headcount_delta": 0.90}},

    {"source": "isbsg", "duration_type": "program", "project_type": "saas_v2_rewrite",
     "planned_budget": 500000, "actual_budget": 600000, "overrun_pct": 0.20,
     "team_size": 10, "duration_days": 270,
     "phase_cost_breakdown": {"1_of_3": 0.20, "2_of_3": 0.48, "3_of_3": 1.0},
     "signal_values_at_overrun": {"phase_slip_days": 0.18, "budget_acceleration": 0.22, "headcount_delta": 0.15}},
]


def upgrade() -> None:
    table = sa.table('historical_projects',
        sa.column('id', sa.Text),
        sa.column('org_id', sa.Text),
        sa.column('source', sa.Text),
        sa.column('duration_type', sa.Text),
        sa.column('project_type', sa.Text),
        sa.column('planned_budget', sa.Numeric),
        sa.column('actual_budget', sa.Numeric),
        sa.column('overrun_pct', sa.Numeric),
        sa.column('team_size', sa.Integer),
        sa.column('duration_days', sa.Integer),
        sa.column('phase_cost_breakdown', sa.Text),
        sa.column('signal_values_at_overrun', sa.Text),
    )
    rows = []
    for r in SEED_RECORDS:
        rows.append({
            **r,
            'org_id': None,
            'phase_cost_breakdown': json.dumps(r['phase_cost_breakdown']),
            'signal_values_at_overrun': json.dumps(r['signal_values_at_overrun']),
        })
    op.bulk_insert(table, rows)


def downgrade() -> None:
    op.execute("DELETE FROM historical_projects WHERE source IN ('isbsg', 'nasa')")

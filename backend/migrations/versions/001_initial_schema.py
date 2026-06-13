"""Initial schema — all tables from ERD

Revision ID: 001
Revises:
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── organizations ──────────────────────────────────────────
    op.create_table('organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── users ──────────────────────────────────────────────────
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clerk_user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── departments ────────────────────────────────────────────
    op.create_table('departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('lead_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── projects ───────────────────────────────────────────────
    op.create_table('projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('duration_type', sa.String(50), nullable=False),  # sprint | medium | program
        sa.Column('baseline_task_count', sa.Integer, nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── project_phases ─────────────────────────────────────────
    op.create_table('project_phases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phase_order', sa.Integer, nullable=False, server_default='1'),
        sa.Column('planned_start', sa.Date, nullable=False),
        sa.Column('planned_end', sa.Date, nullable=False),
        sa.Column('actual_start', sa.Date, nullable=True),
        sa.Column('actual_end', sa.Date, nullable=True),
        sa.Column('budget_allocation_pct', sa.Numeric(5, 2), nullable=False),  # e.g. 25.00 = 25%
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── budgets ────────────────────────────────────────────────
    op.create_table('budgets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('headcount_pct', sa.Numeric(5, 2), nullable=False, server_default='60.00'),
        sa.Column('tools_pct', sa.Numeric(5, 2), nullable=False, server_default='15.00'),
        sa.Column('contractors_pct', sa.Numeric(5, 2), nullable=False, server_default='20.00'),
        sa.Column('contingency_pct', sa.Numeric(5, 2), nullable=False, server_default='5.00'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── time_entries ───────────────────────────────────────────
    op.create_table('time_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('phase_id', UUID(as_uuid=True), sa.ForeignKey('project_phases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('entry_date', sa.Date, nullable=False),
        sa.Column('hours', sa.Numeric(6, 2), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('cost', sa.Numeric(12, 2), sa.Computed('hours * hourly_rate'), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),  # manual|trello|jira|github|linear
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── tool_costs ─────────────────────────────────────────────
    op.create_table('tool_costs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tool_name', sa.String(255), nullable=False),
        sa.Column('monthly_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('active_from', sa.Date, nullable=False),
        sa.Column('active_to', sa.Date, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── contractor_costs ───────────────────────────────────────
    op.create_table('contractor_costs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contractor_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(255), nullable=True),
        sa.Column('daily_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('reason_added', sa.String(100), nullable=False, server_default='planned'),  # deadline_pressure|skill_gap|scope_expansion|planned
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── tool_connections ───────────────────────────────────────
    op.create_table('tool_connections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # trello|jira|github|linear
        sa.Column('access_token', sa.Text, nullable=False),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('config', JSONB, nullable=False, server_default='{}'),
        sa.Column('last_synced_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('org_id', 'provider', name='uq_tool_connections_org_provider'),
    )

    # ── imported_tasks ─────────────────────────────────────────
    op.create_table('imported_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_id', UUID(as_uuid=True), sa.ForeignKey('tool_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='todo'),  # todo|in_progress|completed
        sa.Column('estimated_hours', sa.Numeric(6, 2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(6, 2), nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_overdue', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('synced_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('project_id', 'connection_id', 'external_id', name='uq_imported_tasks_external'),
    )

    # ── historical_projects ────────────────────────────────────
    op.create_table('historical_projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),  # NULL = seed data
        sa.Column('source', sa.String(100), nullable=False, server_default='org'),  # org|isbsg|nasa
        sa.Column('duration_type', sa.String(50), nullable=False),
        sa.Column('project_type', sa.String(100), nullable=True),
        sa.Column('planned_budget', sa.Numeric(14, 2), nullable=True),
        sa.Column('actual_budget', sa.Numeric(14, 2), nullable=True),
        sa.Column('overrun_pct', sa.Numeric(7, 4), nullable=True),  # e.g. 0.2700 = 27%
        sa.Column('team_size', sa.Integer, nullable=True),
        sa.Column('duration_days', sa.Integer, nullable=True),
        sa.Column('phase_cost_breakdown', JSONB, nullable=False, server_default='{}'),
        sa.Column('signal_values_at_overrun', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── forecast_snapshots ─────────────────────────────────────
    op.create_table('forecast_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tier', sa.String(10), nullable=False),  # 1|2|3a|3b
        sa.Column('data_points', sa.Integer, nullable=False),
        sa.Column('baseline_forecast', sa.Numeric(14, 2), nullable=True),
        sa.Column('pressure_multiplier', sa.Numeric(6, 4), nullable=False, server_default='1.0000'),
        sa.Column('final_forecast', sa.Numeric(14, 2), nullable=True),
        sa.Column('predicted_breach_date', sa.Date, nullable=True),
        sa.Column('confidence_score', sa.Numeric(4, 3), nullable=False),  # 0.000 - 1.000
        sa.Column('daily_burn_rate', sa.Numeric(12, 2), nullable=True),
        sa.Column('burn_ratio', sa.Numeric(6, 4), nullable=True),
        sa.Column('signal_values', JSONB, nullable=False, server_default='{}'),
    )


def downgrade() -> None:
    op.drop_table('forecast_snapshots')
    op.drop_table('historical_projects')
    op.drop_table('imported_tasks')
    op.drop_table('tool_connections')
    op.drop_table('contractor_costs')
    op.drop_table('tool_costs')
    op.drop_table('time_entries')
    op.drop_table('budgets')
    op.drop_table('project_phases')
    op.drop_table('projects')
    op.drop_table('departments')
    op.drop_table('users')
    op.drop_table('organizations')

"""Performance indexes

Revision ID: 002
Revises: 001
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Core multi-tenant lookup — every query starts here
    op.create_index('idx_projects_org', 'projects', ['org_id'])
    op.create_index('idx_users_org', 'users', ['org_id'])
    op.create_index('idx_departments_org', 'departments', ['org_id'])

    # Burn rate queries — composite on project + date for range scans
    op.create_index('idx_time_entries_project_date', 'time_entries', ['project_id', 'entry_date'])
    op.create_index('idx_time_entries_user', 'time_entries', ['user_id'])
    op.create_index('idx_time_entries_source', 'time_entries', ['project_id', 'source'])

    # Forecast history — most recent first per project
    op.create_index('idx_forecast_snapshots_project_time',
                    'forecast_snapshots', ['project_id', 'snapshot_at'],
                    postgresql_ops={'snapshot_at': 'DESC'})

    # Integration sync — check for existing tasks before upsert
    op.create_index('idx_imported_tasks_project', 'imported_tasks', ['project_id', 'status'])
    op.create_index('idx_imported_tasks_external', 'imported_tasks', ['connection_id', 'external_id'])

    # Cost queries — active contractors/tools during a date range
    op.create_index('idx_contractor_costs_project_dates',
                    'contractor_costs', ['project_id', 'start_date', 'end_date'])
    op.create_index('idx_tool_costs_project_dates',
                    'tool_costs', ['project_id', 'active_from', 'active_to'])

    # Phase queries
    op.create_index('idx_project_phases_project_order',
                    'project_phases', ['project_id', 'phase_order'])

    # Historical calibration lookup
    op.create_index('idx_historical_projects_org_type',
                    'historical_projects', ['org_id', 'duration_type'])
    op.create_index('idx_historical_projects_source',
                    'historical_projects', ['source', 'duration_type'])

    # Tool connections — one per provider per org
    op.create_index('idx_tool_connections_org',
                    'tool_connections', ['org_id', 'provider'])


def downgrade() -> None:
    indexes = [
        'idx_projects_org', 'idx_users_org', 'idx_departments_org',
        'idx_time_entries_project_date', 'idx_time_entries_user', 'idx_time_entries_source',
        'idx_forecast_snapshots_project_time',
        'idx_imported_tasks_project', 'idx_imported_tasks_external',
        'idx_contractor_costs_project_dates', 'idx_tool_costs_project_dates',
        'idx_project_phases_project_order',
        'idx_historical_projects_org_type', 'idx_historical_projects_source',
        'idx_tool_connections_org',
    ]
    for idx in indexes:
        op.drop_index(idx)

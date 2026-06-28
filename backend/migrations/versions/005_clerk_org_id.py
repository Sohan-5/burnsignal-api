"""Add clerk_org_id to organizations for Clerk auth sync

Revision ID: 005
Revises: 004
Create Date: 2026-06-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('clerk_org_id', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_organizations_clerk_org_id', 'organizations', ['clerk_org_id'])


def downgrade() -> None:
    op.drop_constraint('uq_organizations_clerk_org_id', 'organizations', type_='unique')
    op.drop_column('organizations', 'clerk_org_id')

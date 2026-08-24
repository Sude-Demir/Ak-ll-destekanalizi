"""add assigned_agent_id to tickets

Revision ID: ac6dd06c3067
Revises: d2bb41357916
Create Date: 2026-08-24 11:15:15.589075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac6dd06c3067'
down_revision: Union[str, None] = 'd2bb41357916'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('assigned_agent_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=True))
    op.create_index('ix_tickets_assigned_agent_id', 'tickets', ['assigned_agent_id'])


def downgrade() -> None:
    op.drop_index('ix_tickets_assigned_agent_id', table_name='tickets')
    op.drop_column('tickets', 'assigned_agent_id')

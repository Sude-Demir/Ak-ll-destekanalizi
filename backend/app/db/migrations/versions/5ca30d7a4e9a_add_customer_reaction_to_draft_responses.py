"""add customer_reaction to draft_responses

Revision ID: 5ca30d7a4e9a
Revises: 7d20826fb1f5
Create Date: 2026-08-24 10:58:36.680191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca30d7a4e9a'
down_revision: Union[str, None] = '7d20826fb1f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('draft_responses', sa.Column('customer_reaction', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('draft_responses', 'customer_reaction')

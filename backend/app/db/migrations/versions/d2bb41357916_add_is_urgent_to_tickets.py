"""add is_urgent to tickets

Revision ID: d2bb41357916
Revises: 5ca30d7a4e9a
Create Date: 2026-08-24 11:06:42.377529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2bb41357916'
down_revision: Union[str, None] = '5ca30d7a4e9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('is_urgent', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('tickets', 'is_urgent')

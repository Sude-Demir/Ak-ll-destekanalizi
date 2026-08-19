"""create agents table, add tickets.submitted_by_user_id

Revision ID: f3a8c91d5e22
Revises: c265df391716
Create Date: 2026-08-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a8c91d5e22'
down_revision: Union[str, None] = 'c265df391716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clerk_user_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_agents_clerk_user_id", "agents", ["clerk_user_id"], unique=True)

    op.add_column("tickets", sa.Column("submitted_by_user_id", sa.String(length=255), nullable=True))
    op.create_index("ix_tickets_submitted_by_user_id", "tickets", ["submitted_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_submitted_by_user_id", table_name="tickets")
    op.drop_column("tickets", "submitted_by_user_id")

    op.drop_index("ix_agents_clerk_user_id", table_name="agents")
    op.drop_table("agents")

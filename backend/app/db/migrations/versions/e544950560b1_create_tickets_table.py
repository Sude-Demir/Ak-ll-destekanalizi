"""create tickets table

Revision ID: e544950560b1
Revises: 
Create Date: 2026-08-17 10:03:26.572615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e544950560b1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False, server_default="email"),
        # Hafta 3'te sınıflandırma servisi tarafından doldurulacak.
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_table("tickets")

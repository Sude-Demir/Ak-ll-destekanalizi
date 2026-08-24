"""create ticket_messages table

Revision ID: 1f76048757cf
Revises: ac6dd06c3067
Create Date: 2026-08-24 11:26:59.838883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f76048757cf'
down_revision: Union[str, None] = 'ac6dd06c3067'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ticket_messages_ticket_id", "ticket_messages", ["ticket_id"])
    op.create_index("ix_ticket_messages_created_at", "ticket_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ticket_messages_created_at", table_name="ticket_messages")
    op.drop_index("ix_ticket_messages_ticket_id", table_name="ticket_messages")
    op.drop_table("ticket_messages")

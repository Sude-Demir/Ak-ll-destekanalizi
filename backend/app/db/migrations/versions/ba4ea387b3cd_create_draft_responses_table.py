"""create draft responses table

Revision ID: ba4ea387b3cd
Revises: 24f61267ab34
Create Date: 2026-08-17 15:22:31.318592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba4ea387b3cd'
down_revision: Union[str, None] = '24f61267ab34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "draft_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("retrieved_context", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
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
    op.create_index("ix_draft_responses_ticket_id", "draft_responses", ["ticket_id"])
    op.create_index("ix_draft_responses_status", "draft_responses", ["status"])


def downgrade() -> None:
    op.drop_index("ix_draft_responses_status", table_name="draft_responses")
    op.drop_index("ix_draft_responses_ticket_id", table_name="draft_responses")
    op.drop_table("draft_responses")

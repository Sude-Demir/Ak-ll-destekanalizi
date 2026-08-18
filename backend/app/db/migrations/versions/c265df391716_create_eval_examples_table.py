"""create eval examples table

Revision ID: c265df391716
Revises: ba4ea387b3cd
Create Date: 2026-08-18 15:10:08.208691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c265df391716'
down_revision: Union[str, None] = 'ba4ea387b3cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eval_examples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("expected_category", sa.String(length=50), nullable=False),
        sa.Column("expected_answer_summary", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_eval_examples_ticket_id", "eval_examples", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_eval_examples_ticket_id", table_name="eval_examples")
    op.drop_table("eval_examples")

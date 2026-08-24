"""create kb_suggestions table

Revision ID: 7d20826fb1f5
Revises: 6039796fb7fb
Create Date: 2026-08-24 10:50:26.897526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d20826fb1f5'
down_revision: Union[str, None] = '6039796fb7fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kb_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("kb_chunk_id", sa.Integer(), sa.ForeignKey("knowledge_base_chunks.id"), nullable=True),
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
    op.create_index("ix_kb_suggestions_company_id", "kb_suggestions", ["company_id"])
    op.create_index("ix_kb_suggestions_ticket_id", "kb_suggestions", ["ticket_id"])
    op.create_index("ix_kb_suggestions_status", "kb_suggestions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_kb_suggestions_status", table_name="kb_suggestions")
    op.drop_index("ix_kb_suggestions_ticket_id", table_name="kb_suggestions")
    op.drop_index("ix_kb_suggestions_company_id", table_name="kb_suggestions")
    op.drop_table("kb_suggestions")

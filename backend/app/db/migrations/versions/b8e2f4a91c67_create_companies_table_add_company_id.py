"""create companies table, add company_id to tickets/kb_chunks/agents/agent_invites

Revision ID: b8e2f4a91c67
Revises: a7c4e9f18b3d
Create Date: 2026-08-19 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e2f4a91c67'
down_revision: Union[str, None] = 'a7c4e9f18b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COMPANY_SCOPED_TABLES = ("tickets", "knowledge_base_chunks", "agents", "agent_invites")


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)

    # Mevcut tüm veriyi (300 talep, 27 SSS parçası, mevcut temsilci) sahiplenecek
    # tek bir "bootstrap" şirket. İsim/slug placeholder — sonradan
    # `UPDATE companies SET slug=..., name=... WHERE slug='genel'` ile
    # kolayca değiştirilebilir.
    op.execute("INSERT INTO companies (slug, name) VALUES ('genel', 'Genel Şirket')")

    for table_name in COMPANY_SCOPED_TABLES:
        op.add_column(table_name, sa.Column("company_id", sa.Integer(), nullable=True))
        op.execute(
            f"UPDATE {table_name} SET company_id = (SELECT id FROM companies WHERE slug = 'genel')"
        )
        op.alter_column(table_name, "company_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table_name}_company_id", table_name, "companies", ["company_id"], ["id"]
        )
        op.create_index(f"ix_{table_name}_company_id", table_name, ["company_id"])


def downgrade() -> None:
    for table_name in COMPANY_SCOPED_TABLES:
        op.drop_index(f"ix_{table_name}_company_id", table_name=table_name)
        op.drop_constraint(f"fk_{table_name}_company_id", table_name, type_="foreignkey")
        op.drop_column(table_name, "company_id")

    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_table("companies")

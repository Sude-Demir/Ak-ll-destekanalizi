"""create knowledge base chunks table

Revision ID: 24f61267ab34
Revises: e544950560b1
Create Date: 2026-08-17 15:06:28.789078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '24f61267ab34'
down_revision: Union[str, None] = 'e544950560b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Google Gemini'nin text-embedding-004 modeli 768 boyutlu vektör üretir.
EMBEDDING_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_base_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="manual"),
        # Hafta 3'te embedding üretim fonksiyonu tarafından doldurulacak; şimdilik NULL.
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_knowledge_base_chunks_intent", "knowledge_base_chunks", ["intent"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_base_chunks_intent", table_name="knowledge_base_chunks")
    op.drop_table("knowledge_base_chunks")
    op.execute("DROP EXTENSION IF EXISTS vector")

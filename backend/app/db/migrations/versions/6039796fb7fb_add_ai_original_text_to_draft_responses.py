"""add ai_original_text to draft_responses

Revision ID: 6039796fb7fb
Revises: 38a435c6833a
Create Date: 2026-08-24 10:31:55.113400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6039796fb7fb'
down_revision: Union[str, None] = '38a435c6833a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('draft_responses', sa.Column('ai_original_text', sa.Text(), nullable=True))
    # Mevcut satırlarda AI'nin ilk ürettiği metin ayrıca saklanmadığı için,
    # geriye dönük olarak elimizdeki tek bilgiyi (o anki draft_text) kopyalıyoruz.
    # Bu satırlar için "hiç düzenlenmedi" varsayımıyla tutarlı (zaten
    # draft_text == ai_original_text ise frontend farkı göstermeyecek).
    op.execute("UPDATE draft_responses SET ai_original_text = draft_text WHERE ai_original_text IS NULL")
    op.alter_column('draft_responses', 'ai_original_text', nullable=False)


def downgrade() -> None:
    op.drop_column('draft_responses', 'ai_original_text')

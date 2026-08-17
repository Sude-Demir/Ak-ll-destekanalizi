"""Bir müşteri talebine anlamca en yakın bilgi tabanı parçalarını bulur (RAG'in
"retrieval" / "getirme" kısmı).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseChunk
from app.services.embeddings import embed_text

DEFAULT_TOP_K = 3


def retrieve_relevant_chunks(
    query_text: str, db: Session, top_k: int = DEFAULT_TOP_K
) -> list[KnowledgeBaseChunk]:
    """`query_text`e (örn. bir talebin konu+içerik metni) anlamca en yakın `top_k`
    bilgi tabanı parçasını, pgvector'ın kosinüs mesafesi operatörüyle bulur.

    embedding'i henüz üretilmemiş (NULL) kayıtlar aramaya dahil edilmez.
    """
    query_embedding = embed_text(query_text)
    stmt = (
        select(KnowledgeBaseChunk)
        .filter(KnowledgeBaseChunk.embedding.is_not(None))
        .order_by(KnowledgeBaseChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list(db.scalars(stmt))

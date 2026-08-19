"""Bir müşteri talebine anlamca en yakın bilgi tabanı parçalarını bulur (RAG'in
"retrieval" / "getirme" kısmı).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseChunk
from app.services.embeddings import embed_text

DEFAULT_TOP_K = 3


def retrieve_relevant_chunks(
    query_text: str, company_id: int, db: Session, top_k: int = DEFAULT_TOP_K
) -> list[KnowledgeBaseChunk]:
    """`query_text`e (örn. bir talebin konu+içerik metni) anlamca en yakın `top_k`
    bilgi tabanı parçasını, pgvector'ın kosinüs mesafesi operatörüyle bulur.

    Sadece `company_id`'ye ait parçalar aranır — bir şirketin taslağı başka
    bir şirketin SSS'ine asla dayanmasın diye (bkz. plan "RAG izolasyonu").
    embedding'i henüz üretilmemiş (NULL) kayıtlar aramaya dahil edilmez.
    """
    return [
        chunk for chunk, _distance in retrieve_relevant_chunks_with_distances(query_text, company_id, db, top_k)
    ]


def retrieve_relevant_chunks_with_distances(
    query_text: str, company_id: int, db: Session, top_k: int = DEFAULT_TOP_K
) -> list[tuple[KnowledgeBaseChunk, float]]:
    """`retrieve_relevant_chunks` ile aynı aramayı yapar, ama her parçanın yanında
    pgvector kosinüs mesafesini de döner (bkz. app.services.confidence).
    """
    query_embedding = embed_text(query_text)
    distance = KnowledgeBaseChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(KnowledgeBaseChunk, distance)
        .filter(
            KnowledgeBaseChunk.company_id == company_id,
            KnowledgeBaseChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(top_k)
    )
    return [(chunk, dist) for chunk, dist in db.execute(stmt).all()]

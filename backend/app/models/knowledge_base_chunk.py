import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# Google Gemini'nin text-embedding-004 modeli 768 boyutlu vektör üretir.
# Hafta 3'te gerçek embedding üretimi eklenene kadar bu sütun boş (NULL) kalır.
EMBEDDING_DIM = 768


class KnowledgeBaseChunk(Base):
    """SSS/dokümantasyondan gelen, RAG (retrieval) için kullanılan bir bilgi parçası."""

    __tablename__ = "knowledge_base_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    intent: Mapped[str] = mapped_column(String(100), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100), default="manual")
    # Hafta 3'te embedding üretim fonksiyonu tarafından doldurulacak; şimdilik NULL.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

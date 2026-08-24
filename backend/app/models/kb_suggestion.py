import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class KbSuggestion(Base):
    """Çözülmüş (onaylı/düzenlenmiş yanıtı olan) bir talepten AI'nin ürettiği,
    bir temsilcinin onayını bekleyen SSS (FAQ) taslağı. Onaylanmadan asla
    knowledge_base_chunks'a eklenmez (bkz. CLAUDE.md 'İnsan onaylı akış' —
    bu ilke sadece müşteriye giden yanıtlar için değil, bilgi tabanına
    eklenen içerik için de geçerli)."""

    __tablename__ = "kb_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    intent: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # Onaylanınca oluşturulan gerçek SSS kaydına bağlanır (izlenebilirlik) —
    # reddedilmiş/bekleyen önerilerde NULL kalır.
    kb_chunk_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_base_chunks.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# Bir taslağın "cevaplandı" sayılması için müşteri onaylı (approved) ya da
# temsilci düzenleyip onaylamış (edited) olması gerekir — pending/rejected
# asla cevaplandı sayılmaz (bkz. CLAUDE.md "İnsan onaylı akış"). Bu sabit,
# app.routers.me ve app.routers.tickets arasında paylaşılır.
ANSWERED_DRAFT_STATUSES = ("approved", "edited")


class DraftResponse(Base):
    """Bir talep için AI tarafından üretilen, bir temsilcinin onayını bekleyen
    yanıt taslağı. Hiçbir zaman doğrudan müşteriye gönderilmez — status alanı
    her zaman bir insan kararını yansıtır (bkz. CLAUDE.md "İnsan onaylı akış")."""

    __tablename__ = "draft_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    draft_text: Mapped[str] = mapped_column(Text)
    # AI'nin ilk ürettiği metnin değişmez kopyası — draft_text bir temsilci
    # tarafından düzenlenirse üzerine yazılır, bu alan hep orijinal kalır.
    # Oluşturulduğu anda draft_text ile aynı değerle set edilir (bkz.
    # app.routers.drafts create_draft/bulk_generate_drafts), böylece ikinci
    # bir düzenlemede "gerçek orijinal" kaybolmaz — üzerine yazma mantığı yok.
    ai_original_text: Mapped[str] = mapped_column(Text)
    # Taslağın dayandığı SSS parçalarının içerik kopyası (izlenebilirlik için).
    # bkz. app.services.draft_generation.DraftResult.retrieved_context
    retrieved_context: Mapped[list] = mapped_column(JSON)
    # bkz. app.services.confidence.compute_confidence
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Taslak yazılırken model, sağlanan get_customer_ticket_history aracını
    # gerçekten çağırdı mı (bkz. app.services.draft_generation) — izlenebilirlik.
    used_customer_history: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # Müşterinin portalda bu yanıta verdiği hızlı tepki ("up"/"down") — AI
    # kalitesi hakkında ekip dışından gelen ilk gerçek sinyal. Nullable:
    # çoğu yanıt hiç tepki almaz, bu bir eksiklik değil normal durum.
    customer_reaction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

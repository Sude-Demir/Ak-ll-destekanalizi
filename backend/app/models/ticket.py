import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Ticket(Base):
    """Bir müşteri destek talebini temsil eder (e-posta veya form üzerinden gelir)."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    # Hafta 3'te sınıflandırma servisi tarafından doldurulacak; şimdilik boş kalabilir.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Sınıflandırmayla AYNI LLM çağrısında dolduruluyor (bkz.
    # app.services.classification.ClassificationResult) — talep bir destek
    # sorunundan çok bir satış fırsatı (toplu alım, kurumsal teklif vb.) gibi
    # görünüyorsa true. category gibi henüz sınıflandırılmamışsa varsayılan false.
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Aynı sınıflandırma çağrısında dolduruluyor (bkz. ClassificationResult.is_urgent)
    # — müşteri belirgin şekilde sinirli/tehdit edici bir tonda yazmışsa ya da
    # zamana duyarlı ciddi bir sorun bildiriyorsa true. is_lead ile aynı desen.
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    # Talebi "üstlenmiş" temsilci — birden fazla temsilci aynı talep üzerinde
    # çakışarak çalışmasın diye (bkz. app.routers.tickets update_ticket_assignment).
    # Kimse üstlenmemişse NULL.
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)
    # Talebi giriş yapmış bir müşteri portalından (bkz. app.routers.me) gönderdiyse
    # Clerk kullanıcı kimliği burada tutulur — "kendi taleplerim" sorgusu için.
    # Anonim /support formundan veya e-posta webhook'undan gelen taleplerde NULL kalır.
    submitted_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

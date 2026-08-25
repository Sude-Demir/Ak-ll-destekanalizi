import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Notification(Base):
    """Bir talep sınıflandırılırken lead ya da acil olarak işaretlenince
    oluşan in-app bildirim (bkz. CLAUDE.md 'özgün 10 özellik' listesi #10).

    Belirli bir temsilciye değil, ŞİRKETE ait — küçük bir ekipte kimin
    baktığı önemli değil, biri görüp üstlenene kadar herkese görünür kalması
    yeterli (bkz. app.models.ticket assigned_agent_id ile karıştırılmamalı,
    o ayrı bir kavram). Sadece bir talebin İLK sınıflandırıldığı anda
    oluşturulur (bkz. app.routers.drafts _notify_if_flagged) — aynı talep
    için tekrar tekrar üretilmez.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    type: Mapped[str] = mapped_column(String(20))  # "lead" | "urgent"
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Ticket(Base):
    """Bir müşteri destek talebini temsil eder (e-posta veya form üzerinden gelir)."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    # Hafta 3'te sınıflandırma servisi tarafından doldurulacak; şimdilik boş kalabilir.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

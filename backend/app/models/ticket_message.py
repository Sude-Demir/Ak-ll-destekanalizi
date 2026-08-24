import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TicketMessage(Base):
    """İlk AI destekli yanıttan (draft_responses) SONRA gelen, bir talep
    üzerindeki serbest metin takip mesajı — müşteri ek bilgi/soru yazabilir,
    temsilci doğrudan (AI taslağı olmadan) yanıtlayabilir. draft_responses'a
    dokunmaz; "cevaplandı" tanımı hâlâ sadece onaylı/düzenlenmiş bir taslağa
    dayanır (bkz. app.models.draft_response ANSWERED_DRAFT_STATUSES) — bu
    tablo salt bir konuşma geçmişidir, onay akışının bir parçası değildir."""

    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    sender_type: Mapped[str] = mapped_column(String(20))  # "customer" | "agent"
    # Gönderenin adı, gönderildiği andaki hâliyle sabitlenir (ileride Clerk
    # profili/Agent adı değişse bile geçmiş mesajlar o anki adı göstermeye
    # devam eder).
    sender_name: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

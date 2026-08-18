import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

from app.services.confidence import needs_escalation


class TicketRead(BaseModel):
    """API üzerinden dışa dönen ticket temsili (giriş/çıkış doğrulaması)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_email: str
    subject: str
    body: str
    channel: str
    category: str | None
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DraftResponseRead(BaseModel):
    """API üzerinden dışa dönen taslak yanıt temsili."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    draft_text: str
    retrieved_context: list[dict]
    confidence_score: float | None
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @computed_field
    @property
    def needs_escalation(self) -> bool:
        """Güven skoru eşiğin altındaysa true döner (bkz.
        app.services.confidence.ESCALATION_THRESHOLD). Skor henüz yoksa
        (confidence_score=None) temkinli davranıp true döner."""
        return self.confidence_score is None or needs_escalation(self.confidence_score)


class DraftStatusUpdate(BaseModel):
    """Bir temsilcinin taslak üzerindeki kararı: onayla, düzenleyerek onayla
    veya reddet (bkz. CLAUDE.md "İnsan onaylı akış")."""

    status: Literal["approved", "edited", "rejected"]
    # Sadece status="edited" iken kullanılır: temsilcinin düzenlediği son metin.
    draft_text: str | None = None


class PostmarkFromFull(BaseModel):
    """Postmark'ın inbound webhook payload'undaki gönderen bilgisi."""

    model_config = ConfigDict(extra="ignore")

    Email: str
    Name: str = ""


class InboundEmailPayload(BaseModel):
    """Postmark'ın gelen e-posta webhook'unun gönderdiği JSON — sadece bizim
    kullandığımız alanlar tanımlı, geri kalanı yok sayılır (Postmark onlarca
    ek alan gönderir: Attachments, Headers, MessageID vb.).
    https://postmarkapp.com/developer/webhooks/inbound-webhook
    """

    model_config = ConfigDict(extra="ignore")

    From: str
    FromFull: PostmarkFromFull
    Subject: str = ""
    TextBody: str = ""

import datetime

from pydantic import BaseModel, ConfigDict


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

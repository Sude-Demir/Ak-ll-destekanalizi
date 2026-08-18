"""Kimlik doğrulaması GEREKTİRMEYEN, herkese açık uç noktalar.

Gerçek müşteriler bir Clerk hesabına sahip değildir — bu router bilinçli
olarak `require_auth`/`verify_webhook_auth` kullanmaz, tıpkı bir şirketin
herkese açık "Bize Ulaşın" formu gibi.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Ticket
from app.schemas import PublicTicketCreate, TicketRead

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/tickets", response_model=TicketRead)
def submit_support_request(payload: PublicTicketCreate, db: Session = Depends(get_db)) -> Ticket:
    """Müşterinin herkese açık destek formu üzerinden gönderdiği talebi
    kaydeder (bkz. frontend /support sayfası).
    """
    ticket = Ticket(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        body=payload.body,
        channel="form",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.ticket import Ticket
from app.schemas import TicketRead

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)) -> list[Ticket]:
    """Tüm destek taleplerini en yeniden eskiye doğru listeler."""
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    """Tek bir destek talebinin detayını döner."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return ticket

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, DraftResponse, Ticket
from app.models.draft_response import ANSWERED_DRAFT_STATUSES
from app.schemas import TicketRead

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(require_agent)])


def _answered_exists_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, "onaylı/düzenlenmiş bir taslağı
    var mı" sorusuna cevap veren EXISTS ifadesi. Talep başına ayrı sorgu
    atmak yerine (N+1) tek sorguda hesaplanır — dashboard tek seferde 300
    talebi listeleyebiliyor, bu yüzden performans önemli."""
    return (
        exists()
        .where(DraftResponse.ticket_id == Ticket.id)
        .where(DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
    )


@router.get("", response_model=list[TicketRead])
def list_tickets(agent: Agent = Depends(require_agent), db: Session = Depends(get_db)) -> list[TicketRead]:
    """Temsilcinin KENDİ şirketine ait talepleri en yeniden eskiye doğru,
    cevaplanma durumuyla birlikte listeler (bkz. CLAUDE.md "İnsan onaylı
    akış" ve plan "RAG izolasyonu" — aynı prensip talep listesi için de
    geçerli)."""
    stmt = (
        select(Ticket, _answered_exists_clause().label("is_answered"))
        .filter(Ticket.company_id == agent.company_id)
        .order_by(Ticket.created_at.desc())
    )
    results = []
    for ticket, is_answered in db.execute(stmt).all():
        data = TicketRead.model_validate(ticket)
        data.is_answered = bool(is_answered)
        results.append(data)
    return results


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> TicketRead:
    """Tek bir destek talebinin detayını, cevaplanma durumuyla birlikte döner.
    Talep başka bir şirkete aitse, var olduğu bile sızdırılmadan 404 döner."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.company_id != agent.company_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")

    # Not: _answered_exists_clause() dış sorguda bir Ticket satırı olduğunda
    # (list_tickets'taki gibi) doğru ilişkilendirilir; burada tek bir talep
    # sorgulandığı için ticket_id'yi doğrudan literal değer olarak filtreliyoruz.
    is_answered = db.execute(
        select(
            exists()
            .where(DraftResponse.ticket_id == ticket_id)
            .where(DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
        )
    ).scalar()
    data = TicketRead.model_validate(ticket)
    data.is_answered = bool(is_answered)
    return data

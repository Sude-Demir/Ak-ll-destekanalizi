from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import DraftResponse, Ticket
from app.schemas import DraftResponseRead
from app.services.classification import classify_ticket
from app.services.draft_generation import generate_draft

router = APIRouter(prefix="/tickets", tags=["drafts"])


@router.post("/{ticket_id}/draft", response_model=DraftResponseRead)
def create_draft(ticket_id: int, db: Session = Depends(get_db)) -> DraftResponse:
    """Talebi (henüz sınıflandırılmamışsa) sınıflandırır ve bilgi tabanına
    dayanan bir yanıt taslağı üretip onay kuyruğuna (status="pending") ekler.

    Bu uç nokta MÜŞTERİYE hiçbir şey göndermez — sadece bir taslak kaydı
    oluşturur; taslağın onaylanması/düzenlenmesi/reddedilmesi ayrı bir akıştır
    (bkz. CLAUDE.md "İnsan onaylı akış").
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")

    if ticket.category is None:
        ticket.category = classify_ticket(ticket.subject, ticket.body)

    result = generate_draft(ticket, db)

    draft = DraftResponse(
        ticket_id=ticket.id,
        draft_text=result.draft_text,
        retrieved_context=result.retrieved_context,
        status="pending",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/{ticket_id}/drafts", response_model=list[DraftResponseRead])
def list_drafts(ticket_id: int, db: Session = Depends(get_db)) -> list[DraftResponse]:
    """Bir talebe ait taslakları en yeniden eskiye doğru listeler."""
    stmt = (
        select(DraftResponse)
        .filter(DraftResponse.ticket_id == ticket_id)
        .order_by(DraftResponse.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())

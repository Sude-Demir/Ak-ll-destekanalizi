from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import DraftResponse, Ticket
from app.schemas import DraftResponseRead, DraftStatusUpdate
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
        confidence_score=result.confidence_score,
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


@router.patch("/{ticket_id}/drafts/{draft_id}", response_model=DraftResponseRead)
def update_draft_status(
    ticket_id: int, draft_id: int, payload: DraftStatusUpdate, db: Session = Depends(get_db)
) -> DraftResponse:
    """Bir temsilcinin taslak üzerindeki kararını kaydeder: onayla, düzenleyerek
    onayla veya reddet.

    Bu uç nokta da MÜŞTERİYE hiçbir şey göndermez (bkz. CLAUDE.md "İnsan onaylı
    akış") — sadece kararı draft_responses'a işler.
    """
    draft = db.get(DraftResponse, draft_id)
    if draft is None or draft.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")

    if payload.status == "edited":
        if not payload.draft_text or not payload.draft_text.strip():
            raise HTTPException(status_code=422, detail="Düzenlenmiş taslak metni boş olamaz")
        draft.draft_text = payload.draft_text

    draft.status = payload.status
    db.commit()
    db.refresh(draft)
    return draft

from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors as genai_errors
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, DraftResponse, Ticket
from app.schemas import (
    BulkApproveRequest,
    BulkApproveResult,
    BulkGenerateResult,
    DraftResponseRead,
    DraftStatusUpdate,
)
from app.services.classification import classify_ticket
from app.services.draft_generation import generate_draft

router = APIRouter(prefix="/tickets", tags=["drafts"], dependencies=[Depends(require_agent)])


def _get_own_ticket(ticket_id: int, agent: Agent, db: Session) -> Ticket:
    """Talebi getirir; yoksa ya da başka bir şirkete aitse 404 (var olduğu
    bile sızdırılmaz — bkz. plan 'Kiracı izolasyonu')."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.company_id != agent.company_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return ticket


@router.post("/{ticket_id}/draft", response_model=DraftResponseRead)
def create_draft(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> DraftResponse:
    """Talebi (henüz sınıflandırılmamışsa) sınıflandırır ve bilgi tabanına
    dayanan bir yanıt taslağı üretip onay kuyruğuna (status="pending") ekler.

    Bu uç nokta MÜŞTERİYE hiçbir şey göndermez — sadece bir taslak kaydı
    oluşturur; taslağın onaylanması/düzenlenmesi/reddedilmesi ayrı bir akıştır
    (bkz. CLAUDE.md "İnsan onaylı akış").
    """
    ticket = _get_own_ticket(ticket_id, agent, db)

    if ticket.category is None:
        classification = classify_ticket(ticket.subject, ticket.body)
        ticket.category = classification.category
        ticket.is_lead = classification.is_lead
        ticket.is_urgent = classification.is_urgent

    result = generate_draft(ticket, db)

    draft = DraftResponse(
        ticket_id=ticket.id,
        draft_text=result.draft_text,
        ai_original_text=result.draft_text,
        retrieved_context=result.retrieved_context,
        confidence_score=result.confidence_score,
        used_customer_history=result.used_customer_history,
        status="pending",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/{ticket_id}/drafts", response_model=list[DraftResponseRead])
def list_drafts(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> list[DraftResponse]:
    """Bir talebe ait taslakları en yeniden eskiye doğru listeler."""
    _get_own_ticket(ticket_id, agent, db)

    stmt = (
        select(DraftResponse)
        .filter(DraftResponse.ticket_id == ticket_id)
        .order_by(DraftResponse.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.patch("/{ticket_id}/drafts/{draft_id}", response_model=DraftResponseRead)
def update_draft_status(
    ticket_id: int,
    draft_id: int,
    payload: DraftStatusUpdate,
    agent: Agent = Depends(require_agent),
    db: Session = Depends(get_db),
) -> DraftResponse:
    """Bir temsilcinin taslak üzerindeki kararını kaydeder: onayla, düzenleyerek
    onayla veya reddet.

    Bu uç nokta da MÜŞTERİYE hiçbir şey göndermez (bkz. CLAUDE.md "İnsan onaylı
    akış") — sadece kararı draft_responses'a işler.
    """
    _get_own_ticket(ticket_id, agent, db)

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


@router.post("/bulk-approve", response_model=BulkApproveResult)
def bulk_approve_tickets(
    payload: BulkApproveRequest, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> BulkApproveResult:
    """Birden fazla talebin PENDING durumdaki taslağını tek seferde onaylar
    (bkz. frontend TicketsTable "Seçilenleri Onayla"). Bulunamayan, başka
    şirkete ait ya da pending taslağı olmayan id'ler sessizce `skipped`e
    düşer — hata fırlatmaz, kısmi başarı toleranslıdır."""
    own_ticket_ids = set(
        db.execute(
            select(Ticket.id).filter(Ticket.id.in_(payload.ticket_ids), Ticket.company_id == agent.company_id)
        )
        .scalars()
        .all()
    )

    approved: list[int] = []
    skipped: list[int] = []
    for ticket_id in payload.ticket_ids:
        if ticket_id not in own_ticket_ids:
            skipped.append(ticket_id)
            continue
        draft = db.execute(
            select(DraftResponse)
            .filter(DraftResponse.ticket_id == ticket_id, DraftResponse.status == "pending")
            .order_by(DraftResponse.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if draft is None:
            skipped.append(ticket_id)
            continue
        draft.status = "approved"
        approved.append(ticket_id)

    db.commit()
    return BulkApproveResult(approved=approved, skipped=skipped)


@router.post("/bulk-generate-drafts", response_model=BulkGenerateResult)
def bulk_generate_drafts(
    payload: BulkApproveRequest, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> BulkGenerateResult:
    """Hiç taslağı üretilmemiş birden fazla talep için tek seferde AI taslağı
    üretir (bkz. frontend TicketsTable "Seçilenler için Taslak Oluştur").
    Taslaklar yine "pending" olarak eklenir — bu uç nokta hiçbir şeyi
    otomatik onaylamaz (bkz. CLAUDE.md "İnsan onaylı akış").

    Her talep için gerçek bir Gemini çağrısı yapılır — ücretsiz katmanın
    günlük kotası düşük olduğu için (bkz. app/services/llm.py) bazı talepler
    kota/ağ hatasıyla `failed`e düşebilir; bu durumda işlem DURMAZ, sıradaki
    talebe geçilir (kısmi başarı toleranslı, `bulk_approve_tickets` ile aynı
    prensip)."""
    own_ticket_ids = set(
        db.execute(
            select(Ticket.id).filter(Ticket.id.in_(payload.ticket_ids), Ticket.company_id == agent.company_id)
        )
        .scalars()
        .all()
    )

    created: list[int] = []
    skipped: list[int] = []
    failed: list[int] = []
    for ticket_id in payload.ticket_ids:
        if ticket_id not in own_ticket_ids:
            skipped.append(ticket_id)
            continue

        has_pending = db.execute(
            select(exists().where(DraftResponse.ticket_id == ticket_id).where(DraftResponse.status == "pending"))
        ).scalar()
        if has_pending:
            skipped.append(ticket_id)
            continue

        ticket = db.get(Ticket, ticket_id)
        try:
            if ticket.category is None:
                classification = classify_ticket(ticket.subject, ticket.body)
                ticket.category = classification.category
                ticket.is_lead = classification.is_lead
                ticket.is_urgent = classification.is_urgent
            result = generate_draft(ticket, db)
        except genai_errors.APIError:
            failed.append(ticket_id)
            continue

        db.add(
            DraftResponse(
                ticket_id=ticket.id,
                draft_text=result.draft_text,
                ai_original_text=result.draft_text,
                retrieved_context=result.retrieved_context,
                confidence_score=result.confidence_score,
                used_customer_history=result.used_customer_history,
                status="pending",
            )
        )
        created.append(ticket_id)

    db.commit()
    return BulkGenerateResult(created=created, skipped=skipped, failed=failed)

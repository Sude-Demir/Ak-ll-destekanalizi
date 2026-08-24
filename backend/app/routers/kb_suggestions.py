from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, DraftResponse, KbSuggestion, KnowledgeBaseChunk, Ticket
from app.models.draft_response import ANSWERED_DRAFT_STATUSES
from app.schemas import KbSuggestionRead, KbSuggestionStatusUpdate
from app.services.classification import FALLBACK_CATEGORY
from app.services.embeddings import embed_text
from app.services.kb_suggestion_generation import generate_kb_suggestion

router = APIRouter(prefix="/tickets", tags=["kb-suggestions"], dependencies=[Depends(require_agent)])


def _get_own_ticket(ticket_id: int, agent: Agent, db: Session) -> Ticket:
    """Talebi getirir; yoksa ya da başka bir şirkete aitse 404 (var olduğu
    bile sızdırılmaz — bkz. app.routers.drafts aynı desen)."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.company_id != agent.company_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return ticket


def _latest_answered_draft(ticket_id: int, db: Session) -> DraftResponse | None:
    return db.execute(
        select(DraftResponse)
        .filter(DraftResponse.ticket_id == ticket_id, DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
        .order_by(DraftResponse.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


@router.post("/{ticket_id}/kb-suggestion", response_model=KbSuggestionRead)
def create_kb_suggestion(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> KbSuggestion:
    """Çözülmüş bir talepten (onaylı/düzenlenmiş bir yanıtı olan) genelleştirilmiş
    bir SSS taslağı üretir ve onay kuyruğuna (status="pending") ekler.

    Bu uç nokta knowledge_base_chunks'a HİÇBİR ŞEY eklemez (bkz. CLAUDE.md
    "İnsan onaylı akış" — bu ilke sadece müşteriye giden yanıtlar için değil,
    bilgi tabanına eklenen içerik için de geçerli) — sadece bir öneri kaydı
    oluşturur, onaylanması ayrı bir adımdır.
    """
    ticket = _get_own_ticket(ticket_id, agent, db)

    latest_draft = _latest_answered_draft(ticket_id, db)
    if latest_draft is None:
        raise HTTPException(status_code=400, detail="Bu talebin onaylanmış/düzenlenmiş bir yanıtı yok")

    result = generate_kb_suggestion(ticket.subject, ticket.body, latest_draft.draft_text)

    suggestion = KbSuggestion(
        company_id=agent.company_id,
        ticket_id=ticket.id,
        question=result.question,
        answer=result.answer,
        category=ticket.category or FALLBACK_CATEGORY,
        intent=result.intent,
        status="pending",
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.get("/{ticket_id}/kb-suggestions", response_model=list[KbSuggestionRead])
def list_kb_suggestions(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> list[KbSuggestion]:
    """Bir talebe ait SSS önerilerini en yeniden eskiye listeler."""
    _get_own_ticket(ticket_id, agent, db)

    stmt = (
        select(KbSuggestion)
        .filter(KbSuggestion.ticket_id == ticket_id)
        .order_by(KbSuggestion.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.patch("/{ticket_id}/kb-suggestions/{suggestion_id}", response_model=KbSuggestionRead)
def update_kb_suggestion_status(
    ticket_id: int,
    suggestion_id: int,
    payload: KbSuggestionStatusUpdate,
    agent: Agent = Depends(require_agent),
    db: Session = Depends(get_db),
) -> KbSuggestion:
    """Bir temsilcinin SSS önerisi üzerindeki kararı: onayla ya da reddet.
    Onaylanırsa gerçek bir knowledge_base_chunks kaydı oluşturulur ve hemen
    embed edilir (bkz. scripts/embed_kb.py ile aynı `soru+cevap` embedding
    deseni) — tekil bir onay olduğu için toplu script'e gerek yok, senkron
    yapılır. Reddedilirse hiçbir SSS kaydı oluşmaz.
    """
    _get_own_ticket(ticket_id, agent, db)

    suggestion = db.get(KbSuggestion, suggestion_id)
    if suggestion is None or suggestion.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Öneri bulunamadı")

    if payload.question is not None:
        suggestion.question = payload.question
    if payload.answer is not None:
        suggestion.answer = payload.answer

    if payload.status == "approved":
        chunk = KnowledgeBaseChunk(
            company_id=suggestion.company_id,
            category=suggestion.category,
            intent=suggestion.intent,
            question=suggestion.question,
            answer=suggestion.answer,
            source="ticket_suggestion",
            embedding=embed_text(f"{suggestion.question}\n{suggestion.answer}"),
        )
        db.add(chunk)
        db.flush()  # chunk.id'yi commit'ten önce almak için
        suggestion.kb_chunk_id = chunk.id

    suggestion.status = payload.status
    db.commit()
    db.refresh(suggestion)
    return suggestion

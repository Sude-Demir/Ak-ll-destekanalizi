from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db.database import get_db
from app.models import Agent, Company, DraftResponse, Ticket, TicketMessage
from app.models.draft_response import ANSWERED_DRAFT_STATUSES
from app.schemas import (
    MeRead,
    MyTicketCreate,
    MyTicketRead,
    TicketMessageCreate,
    TicketMessageRead,
    TicketReactionUpdate,
)
from app.services.clerk_users import fetch_user_profile

router = APIRouter(prefix="/me", tags=["me"], dependencies=[Depends(require_auth)])


def _latest_answered_draft(db: Session, ticket_id: int) -> DraftResponse | None:
    stmt = (
        select(DraftResponse)
        .filter(DraftResponse.ticket_id == ticket_id, DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
        .order_by(DraftResponse.created_at.desc())
    )
    return db.execute(stmt).scalars().first()


def _to_my_ticket_read(db: Session, ticket: Ticket) -> MyTicketRead:
    # Müşterinin talep sayısı (kendi taleplerinin listesi) küçük olduğu için
    # burada şirket başına ayrı sorgu atmak (agent tarafındaki 300 taleplik
    # dashboard'un aksine) performans sorunu yaratmıyor.
    company = db.get(Company, ticket.company_id)
    draft = _latest_answered_draft(db, ticket.id)
    return MyTicketRead(
        id=ticket.id,
        subject=ticket.subject,
        body=ticket.body,
        created_at=ticket.created_at,
        answer=draft.draft_text if draft else None,
        reaction=draft.customer_reaction if draft else None,
        company_name=company.name,
        company_slug=company.slug,
    )


@router.get("", response_model=MeRead)
def read_me(clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)) -> MeRead:
    """Giriş yapan kişinin temsilci mi müşteri mi olduğunu döner — frontend
    kök sayfada (`/`) buna göre `/dashboard` ya da `/portal`'a yönlendirir."""
    agent = db.execute(select(Agent).filter(Agent.clerk_user_id == clerk_user_id)).scalar_one_or_none()
    if agent is not None:
        company = db.get(Company, agent.company_id)
        return MeRead(clerk_user_id=clerk_user_id, is_agent=True, name=agent.name, company_name=company.name)

    name, _email = fetch_user_profile(clerk_user_id)
    return MeRead(clerk_user_id=clerk_user_id, is_agent=False, name=name)


@router.post("/tickets", response_model=MyTicketRead)
def create_my_ticket(
    payload: MyTicketCreate,
    clerk_user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
) -> MyTicketRead:
    """Giriş yapmış bir müşterinin kendi portalından talep açması. Ad/e-posta
    gövdede istenmez, taklit edilmesin diye Clerk oturumundan okunur (bkz.
    app.services.clerk_users). `payload.company_slug` talebin hangi şirkete
    gideceğini belirtir (bkz. app/portal/new/[slug])."""
    company = db.execute(select(Company).filter(Company.slug == payload.company_slug)).scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı")

    name, email = fetch_user_profile(clerk_user_id)

    ticket = Ticket(
        company_id=company.id,
        customer_name=name,
        customer_email=email,
        subject=payload.subject,
        body=payload.body,
        channel="portal",
        is_lead=False,
        is_urgent=False,
        submitted_by_user_id=clerk_user_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _to_my_ticket_read(db, ticket)


@router.get("/tickets", response_model=list[MyTicketRead])
def list_my_tickets(
    clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> list[MyTicketRead]:
    """Giriş yapan kişinin kendi açtığı talepler, en yeniden eskiye — hangi
    şirkete ait olursa olsun (bir müşteri birden fazla şirkete talep açmış
    olabilir, bkz. plan)."""
    stmt = (
        select(Ticket)
        .filter(Ticket.submitted_by_user_id == clerk_user_id)
        .order_by(Ticket.created_at.desc())
    )
    tickets = db.execute(stmt).scalars().all()
    return [_to_my_ticket_read(db, t) for t in tickets]


def _get_own_ticket(ticket_id: int, clerk_user_id: str, db: Session) -> Ticket:
    """Talebi getirir; yoksa ya da başka bir müşteriye aitse 404 (var olduğu
    bile sızdırılmaz) — get_my_ticket ve update_ticket_reaction arasında
    paylaşılan kontrol."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.submitted_by_user_id != clerk_user_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return ticket


@router.get("/tickets/{ticket_id}", response_model=MyTicketRead)
def get_my_ticket(
    ticket_id: int, clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> MyTicketRead:
    """Tek bir talebin detayı — sadece kendi talebiyse. Talep başkasınaysa ya
    da hiç yoksa aynı 404 dönülür; bir talebin var olup olmadığı bile
    sızdırılmaz."""
    ticket = _get_own_ticket(ticket_id, clerk_user_id, db)
    return _to_my_ticket_read(db, ticket)


@router.patch("/tickets/{ticket_id}/reaction", response_model=MyTicketRead)
def update_ticket_reaction(
    ticket_id: int,
    payload: TicketReactionUpdate,
    clerk_user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
) -> MyTicketRead:
    """Müşterinin, kendi talebinin yanıtına verdiği hızlı 👍/👎 tepkisini
    kaydeder — AI kalitesi hakkında ekip dışından gelen ilk gerçek sinyal.
    Talebin onaylı/düzenlenmiş bir yanıtı yoksa 400 (tepki verilecek bir şey
    yok)."""
    ticket = _get_own_ticket(ticket_id, clerk_user_id, db)

    draft = _latest_answered_draft(db, ticket.id)
    if draft is None:
        raise HTTPException(status_code=400, detail="Bu talebin henüz bir yanıtı yok")

    draft.customer_reaction = payload.reaction
    db.commit()
    return _to_my_ticket_read(db, ticket)


@router.get("/tickets/{ticket_id}/messages", response_model=list[TicketMessageRead])
def list_my_ticket_messages(
    ticket_id: int, clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> list[TicketMessage]:
    """Müşterinin kendi talebindeki takip mesajlarını en eskiden en yeniye
    listeler (bkz. CLAUDE.md 'özgün 10 özellik' listesi #6)."""
    _get_own_ticket(ticket_id, clerk_user_id, db)
    stmt = (
        select(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/tickets/{ticket_id}/messages", response_model=TicketMessageRead)
def create_my_ticket_message(
    ticket_id: int,
    payload: TicketMessageCreate,
    clerk_user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
) -> TicketMessage:
    """Müşterinin kendi talebine yazdığı bir takip mesajı. Ad, taklit
    edilmesin diye (bkz. create_my_ticket ile aynı gerekçe) Clerk oturumundan
    okunur, gövdede istenmez."""
    ticket = _get_own_ticket(ticket_id, clerk_user_id, db)
    name, _email = fetch_user_profile(clerk_user_id)
    message = TicketMessage(ticket_id=ticket.id, sender_type="customer", sender_name=name, body=payload.body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

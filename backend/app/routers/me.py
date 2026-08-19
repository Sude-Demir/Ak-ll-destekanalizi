from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db.database import get_db
from app.models import Agent, DraftResponse, Ticket
from app.models.draft_response import ANSWERED_DRAFT_STATUSES
from app.schemas import MeRead, MyTicketCreate, MyTicketRead
from app.services.clerk_users import fetch_user_profile

router = APIRouter(prefix="/me", tags=["me"], dependencies=[Depends(require_auth)])


def _latest_answer(db: Session, ticket_id: int) -> str | None:
    stmt = (
        select(DraftResponse.draft_text)
        .filter(DraftResponse.ticket_id == ticket_id, DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
        .order_by(DraftResponse.created_at.desc())
    )
    return db.execute(stmt).scalars().first()


def _to_my_ticket_read(db: Session, ticket: Ticket) -> MyTicketRead:
    return MyTicketRead(
        id=ticket.id,
        subject=ticket.subject,
        body=ticket.body,
        created_at=ticket.created_at,
        answer=_latest_answer(db, ticket.id),
    )


@router.get("", response_model=MeRead)
def read_me(clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)) -> MeRead:
    """Giriş yapan kişinin temsilci mi müşteri mi olduğunu döner — frontend
    kök sayfada (`/`) buna göre `/dashboard` ya da `/portal`'a yönlendirir."""
    agent = db.execute(select(Agent).filter(Agent.clerk_user_id == clerk_user_id)).scalar_one_or_none()
    if agent is not None:
        return MeRead(clerk_user_id=clerk_user_id, is_agent=True, name=agent.name)

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
    app.services.clerk_users)."""
    name, email = fetch_user_profile(clerk_user_id)

    ticket = Ticket(
        customer_name=name,
        customer_email=email,
        subject=payload.subject,
        body=payload.body,
        channel="portal",
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
    """Giriş yapan kişinin kendi açtığı talepler, en yeniden eskiye."""
    stmt = (
        select(Ticket)
        .filter(Ticket.submitted_by_user_id == clerk_user_id)
        .order_by(Ticket.created_at.desc())
    )
    tickets = db.execute(stmt).scalars().all()
    return [_to_my_ticket_read(db, t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=MyTicketRead)
def get_my_ticket(
    ticket_id: int, clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> MyTicketRead:
    """Tek bir talebin detayı — sadece kendi talebiyse. Talep başkasınaysa ya
    da hiç yoksa aynı 404 dönülür; bir talebin var olup olmadığı bile
    sızdırılmaz."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.submitted_by_user_id != clerk_user_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return _to_my_ticket_read(db, ticket)

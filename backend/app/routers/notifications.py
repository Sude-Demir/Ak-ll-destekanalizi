import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, Notification, Ticket
from app.schemas import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(require_agent)])

LIST_LIMIT = 30


def _list_own_notifications(company_id: int, db: Session) -> list[NotificationRead]:
    stmt = (
        select(Notification, Ticket.subject)
        .join(Ticket, Ticket.id == Notification.ticket_id)
        .filter(Notification.company_id == company_id)
        .order_by(Notification.created_at.desc())
        .limit(LIST_LIMIT)
    )
    items = []
    for notification, subject in db.execute(stmt).all():
        data = NotificationRead.model_validate(notification)
        data.ticket_subject = subject
        items.append(data)
    return items


def _mark_all_read(company_id: int, db: Session) -> None:
    db.execute(
        update(Notification)
        .where(Notification.company_id == company_id)
        .where(Notification.read_at.is_(None))
        .values(read_at=datetime.datetime.now(datetime.timezone.utc))
    )
    db.commit()


@router.get("", response_model=list[NotificationRead])
def list_notifications(agent: Agent = Depends(require_agent), db: Session = Depends(get_db)) -> list[NotificationRead]:
    """Şirketin en yeni bildirimlerini döner (bkz. app.models.notification —
    belirli bir temsilciye değil şirkete ait). Bir talebin başlığını da
    taşıması için Ticket'a join'lenir."""
    return _list_own_notifications(agent.company_id, db)


@router.post("/read-all", response_model=list[NotificationRead])
def mark_all_notifications_read(
    agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> list[NotificationRead]:
    """Şirketin okunmamış tüm bildirimlerini okundu işaretler (bkz. frontend
    NotificationBell — dropdown açılınca çağrılır). Güncel listeyi döner ki
    frontend ekstra bir GET atmasın."""
    _mark_all_read(agent.company_id, db)
    return _list_own_notifications(agent.company_id, db)

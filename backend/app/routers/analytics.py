from fastapi import APIRouter, Depends
from sqlalchemy import case, exists, func, select
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, DraftResponse, Ticket
from app.routers.tickets import answered_exists_clause
from app.schemas import AnalyticsRead, DailyTicketCount, DraftTotals, TicketTotals
from app.services.confidence import ESCALATION_THRESHOLD

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_agent)])

# Zaman içindeki hacim grafiğinde gösterilecek en fazla gün sayısı. Seed veri
# (Kaggle) 2017 tarihli olduğu için "bugünden geriye 30 gün" değil, veride
# mevcut EN SON 30 gün alınır (bkz. _daily_ticket_counts).
DAILY_CHART_DAYS = 30


def _without_draft_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, "hiç taslak üretilmemiş" sorusuna
    cevap veren ifade. answered_exists_clause()'dan farklı olarak taslağın
    durumuna bakmaz — hiç var olup olmadığına bakar."""
    return ~exists().where(DraftResponse.ticket_id == Ticket.id)


def _ticket_totals(company_id: int, db: Session) -> TicketTotals:
    stmt = select(
        func.count().label("total"),
        func.sum(case((answered_exists_clause(), 1), else_=0)).label("answered"),
        func.sum(case((_without_draft_clause(), 1), else_=0)).label("without_draft"),
    ).select_from(Ticket).filter(Ticket.company_id == company_id)
    row = db.execute(stmt).one()
    return TicketTotals(
        total=row.total,
        answered=row.answered or 0,
        without_draft=row.without_draft or 0,
    )


def _draft_totals(company_id: int, db: Session) -> DraftTotals:
    # Düşük güvenden eskalasyona düşme tanımı schemas.DraftResponseRead.needs_escalation
    # ile aynı: skor eşiğin altındaysa VEYA henüz hesaplanmadıysa (None) temkinli
    # davranılıp eskalasyon sayılır.
    escalated_clause = (DraftResponse.confidence_score.is_(None)) | (
        DraftResponse.confidence_score < ESCALATION_THRESHOLD
    )
    stmt = (
        select(
            func.count().label("total"),
            func.sum(case((DraftResponse.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((DraftResponse.status == "approved", 1), else_=0)).label("approved"),
            func.sum(case((DraftResponse.status == "edited", 1), else_=0)).label("edited"),
            func.sum(case((DraftResponse.status == "rejected", 1), else_=0)).label("rejected"),
            func.avg(DraftResponse.confidence_score).label("average_confidence"),
            func.sum(case((escalated_clause, 1), else_=0)).label("escalated"),
        )
        .join(Ticket, DraftResponse.ticket_id == Ticket.id)
        .filter(Ticket.company_id == company_id)
    )
    row = db.execute(stmt).one()
    average_confidence = None if row.average_confidence is None else float(row.average_confidence)
    return DraftTotals(
        total=row.total,
        pending=row.pending or 0,
        approved=row.approved or 0,
        edited=row.edited or 0,
        rejected=row.rejected or 0,
        average_confidence=average_confidence,
        escalated=row.escalated or 0,
    )


def _daily_ticket_counts(company_id: int, db: Session) -> list[DailyTicketCount]:
    day = func.date(Ticket.created_at)
    recent_days = (
        select(day.label("day"), func.count().label("count"))
        .filter(Ticket.company_id == company_id)
        .group_by(day)
        .order_by(day.desc())
        .limit(DAILY_CHART_DAYS)
        .subquery()
    )
    stmt = select(recent_days.c.day, recent_days.c.count).order_by(recent_days.c.day.asc())
    rows = db.execute(stmt).all()
    return [DailyTicketCount(date=row.day, count=row.count) for row in rows]


@router.get("", response_model=AnalyticsRead)
def get_analytics(agent: Agent = Depends(require_agent), db: Session = Depends(get_db)) -> AnalyticsRead:
    """Temsilcinin şirketi için toplu performans özeti — talep hacmi, AI
    taslaklarının onay/düzenleme/red dağılımı, ortalama güven skoru ve
    zaman içindeki talep hacmi. Her yardımcı fonksiyon sorgusunu
    `agent.company_id`'ye göre filtreler (bkz. CLAUDE.md "Kiracı izolasyonu")."""
    return AnalyticsRead(
        tickets=_ticket_totals(agent.company_id, db),
        drafts=_draft_totals(agent.company_id, db),
        daily_ticket_counts=_daily_ticket_counts(agent.company_id, db),
    )

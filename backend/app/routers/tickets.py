from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.auth import require_agent
from app.db.database import get_db
from app.models import Agent, DraftResponse, Ticket, TicketMessage
from app.models.draft_response import ANSWERED_DRAFT_STATUSES
from app.schemas import TicketAssignmentUpdate, TicketListRead, TicketMessageCreate, TicketMessageRead, TicketRead

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(require_agent)])

PAGE_SIZE = 50


def _get_own_ticket(ticket_id: int, agent: Agent, db: Session) -> Ticket:
    """Talebi getirir; yoksa ya da başka bir şirkete aitse 404 (var olduğu
    bile sızdırılmaz) — get_ticket, update_ticket_assignment ve mesaj
    uç noktaları arasında paylaşılan kontrol."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.company_id != agent.company_id:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return ticket


def answered_exists_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, "onaylı/düzenlenmiş bir taslağı
    var mı" sorusuna cevap veren EXISTS ifadesi. Talep başına ayrı sorgu
    atmak yerine (N+1) tek sorguda hesaplanır — dashboard tek seferde 300
    talebi listeleyebiliyor, bu yüzden performans önemli. app.routers.analytics
    da aynı "cevaplandı" tanımını kullanmak için bunu import eder."""
    return (
        exists()
        .where(DraftResponse.ticket_id == Ticket.id)
        .where(DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
    )


def pending_draft_id_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, o talebin EN YENİ "pending"
    durumdaki taslağının id'sini döndüren scalar subquery — yoksa NULL.
    Birden fazla pending taslak varsa (nadir bir durum, normalde bir talebin
    tek aktif taslağı olur) en yenisi seçilir. Toplu onay akışı (bkz.
    app.routers.drafts bulk_approve_tickets) hangi taslağın onaylanacağını
    bu alandan bilir."""
    return (
        select(DraftResponse.id)
        .where(DraftResponse.ticket_id == Ticket.id)
        .where(DraftResponse.status == "pending")
        .order_by(DraftResponse.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )


def assigned_agent_name_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, talebi üstlenen temsilcinin
    adını döndüren scalar subquery — kimse üstlenmediyse NULL."""
    return select(Agent.name).where(Agent.id == Ticket.assigned_agent_id).scalar_subquery()


def pending_draft_confidence_clause():
    """Bir `Ticket` satırıyla eşlenebilecek, o talebin en yeni "pending"
    taslağının güven skorunu döndüren scalar subquery — pending taslağı
    yoksa NULL. Otomatik onay/gönderim DEĞİL, sadece `sort=priority`
    sıralaması için (bkz. CLAUDE.md 'özgün 10 özellik' listesi #8) — hangi
    taslağa önce bakılacağını belirler, hiçbir taslağı otomatik onaylamaz."""
    return (
        select(DraftResponse.confidence_score)
        .where(DraftResponse.ticket_id == Ticket.id)
        .where(DraftResponse.status == "pending")
        .order_by(DraftResponse.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )


def _read_ticket_with_computed_fields(ticket: Ticket, db: Session) -> TicketRead:
    """Tek bir Ticket satırından, başka tablolardan/subquery'den gelen
    alanları (is_answered, pending_draft_id, assigned_agent_name) da
    doldurarak bir TicketRead üretir. get_ticket ve update_ticket_assignment
    arasında paylaşılır."""
    is_answered = db.execute(
        select(
            exists()
            .where(DraftResponse.ticket_id == ticket.id)
            .where(DraftResponse.status.in_(ANSWERED_DRAFT_STATUSES))
        )
    ).scalar()
    pending_draft_id = db.execute(
        select(DraftResponse.id)
        .where(DraftResponse.ticket_id == ticket.id)
        .where(DraftResponse.status == "pending")
        .order_by(DraftResponse.created_at.desc())
        .limit(1)
    ).scalar()
    assigned_agent_name = (
        db.execute(select(Agent.name).where(Agent.id == ticket.assigned_agent_id)).scalar()
        if ticket.assigned_agent_id is not None
        else None
    )
    data = TicketRead.model_validate(ticket)
    data.is_answered = bool(is_answered)
    data.pending_draft_id = pending_draft_id
    data.assigned_agent_name = assigned_agent_name
    return data


def _overall_summary(company_id: int, db: Session) -> dict:
    """Arama/kategori filtresinden BAĞIMSIZ, şirketin TÜM talepleri üzerinden
    hesaplanan özet — TicketStats'ın her zaman doğru toplam göstermesi için
    (bkz. TicketListRead docstring'i)."""
    stmt = select(
        func.count().label("total"),
        func.sum(case((Ticket.status == "open", 1), else_=0)).label("open_count"),
        func.sum(case((Ticket.category.is_not(None), 1), else_=0)).label("classified_count"),
        func.sum(case((Ticket.status == "closed", 1), else_=0)).label("resolved_count"),
    ).select_from(Ticket).filter(Ticket.company_id == company_id)
    row = db.execute(stmt).one()
    return {
        "overall_total": row.total,
        "open_count": row.open_count or 0,
        "classified_count": row.classified_count or 0,
        "resolved_count": row.resolved_count or 0,
    }


def _category_counts(company_id: int, db: Session) -> dict[str, int]:
    """Arama/kategori filtresinden BAĞIMSIZ, kategori başına talep sayısı —
    CategoryFilterBar ve CategoryDistribution için (bkz. TicketListRead
    docstring'i)."""
    stmt = (
        select(Ticket.category, func.count())
        .filter(Ticket.company_id == company_id, Ticket.category.is_not(None))
        .group_by(Ticket.category)
    )
    return {category: count for category, count in db.execute(stmt).all()}


@router.get("", response_model=TicketListRead)
def list_tickets(
    q: str | None = None,
    category: str | None = None,
    customer_email: str | None = None,
    channel: str | None = None,
    is_answered: bool | None = None,
    is_lead: bool | None = None,
    is_urgent: bool | None = None,
    sort: str = "newest",
    page: int = 1,
    agent: Agent = Depends(require_agent),
    db: Session = Depends(get_db),
) -> TicketListRead:
    """Temsilcinin KENDİ şirketine ait talepleri isteğe bağlı arama/kategori/
    müşteri/kanal/cevap-durumu/lead/aciliyet filtresiyle ve sayfalanmış olarak listeler
    (bkz. CLAUDE.md "İnsan onaylı akış" ve plan "RAG izolasyonu" — aynı
    prensip talep listesi için de geçerli). `sort` "newest" (varsayılan),
    "oldest" ya da "priority" olabilir, tanınmayan bir değer sessizce
    "newest"e düşer — tıpkı `category` gibi bilinmeyen bir filtre değerinin
    sessizce boş sonuç dönmesi gibi, burada da frontend geçerli değerleri
    zaten kısıtlıyor. "priority": önce acil (`is_urgent`) talepler, sonra
    pending taslağı en düşük güvenli (en belirsiz) olanlar önce gelir —
    HİÇBİR ŞEYİ otomatik onaylamaz/göndermez, sadece bir temsilcinin onay
    kuyruğunda önce hangisine bakması gerektiğini gösterir (bkz. CLAUDE.md
    "özgün 10 özellik" listesi #8). Yanıt ayrıca bu filtrelerden bağımsız bir
    şirket-geneli özet taşır (bkz. TicketListRead)."""
    filters = [Ticket.company_id == agent.company_id]
    if q:
        like = f"%{q}%"
        filters.append(or_(Ticket.subject.ilike(like), Ticket.customer_name.ilike(like), Ticket.body.ilike(like)))
    if category:
        filters.append(Ticket.category == category)
    if customer_email:
        filters.append(Ticket.customer_email == customer_email)
    if channel:
        filters.append(Ticket.channel == channel)
    if is_answered is not None:
        filters.append(answered_exists_clause() if is_answered else ~answered_exists_clause())
    if is_lead is not None:
        filters.append(Ticket.is_lead == is_lead)
    if is_urgent is not None:
        filters.append(Ticket.is_urgent == is_urgent)

    total = db.execute(select(func.count()).select_from(Ticket).filter(*filters)).scalar() or 0

    if sort == "priority":
        order_by = (Ticket.is_urgent.desc(), pending_draft_confidence_clause().asc().nulls_last())
    elif sort == "oldest":
        order_by = (Ticket.created_at.asc(),)
    else:
        order_by = (Ticket.created_at.desc(),)
    stmt = (
        select(
            Ticket,
            answered_exists_clause().label("is_answered"),
            pending_draft_id_clause().label("pending_draft_id"),
            assigned_agent_name_clause().label("assigned_agent_name"),
        )
        .filter(*filters)
        .order_by(*order_by)
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
    items = []
    for ticket, is_answered, pending_draft_id, assigned_agent_name in db.execute(stmt).all():
        data = TicketRead.model_validate(ticket)
        data.is_answered = bool(is_answered)
        data.pending_draft_id = pending_draft_id
        data.assigned_agent_name = assigned_agent_name
        items.append(data)

    summary = _overall_summary(agent.company_id, db)
    category_counts = _category_counts(agent.company_id, db)

    return TicketListRead(
        items=items,
        total=total,
        page=page,
        page_size=PAGE_SIZE,
        category_counts=category_counts,
        **summary,
    )


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> TicketRead:
    """Tek bir destek talebinin detayını, cevaplanma durumuyla birlikte döner.
    Talep başka bir şirkete aitse, var olduğu bile sızdırılmadan 404 döner.

    Not: answered_exists_clause() dış sorguda bir Ticket satırı olduğunda
    (list_tickets'taki gibi) doğru ilişkilendirilir; _read_ticket_with_computed_fields
    burada tek bir talep sorgulandığı için ticket_id'yi doğrudan literal değer
    olarak filtreler."""
    ticket = _get_own_ticket(ticket_id, agent, db)
    return _read_ticket_with_computed_fields(ticket, db)


@router.patch("/{ticket_id}/assignment", response_model=TicketRead)
def update_ticket_assignment(
    ticket_id: int,
    payload: TicketAssignmentUpdate,
    agent: Agent = Depends(require_agent),
    db: Session = Depends(get_db),
) -> TicketRead:
    """Bir temsilcinin talebi üstlenmesi ya da bırakması — birden fazla
    temsilci aynı talep üzerinde çakışarak çalışmasın diye (bkz. CLAUDE.md
    "özgün 10 özellik" listesi #5). `claim=true` talebi ARAYAN temsilciye
    atar (başkasına atanmış olsa bile — devralma serbest); `claim=false`
    atamayı tamamen kaldırır."""
    ticket = _get_own_ticket(ticket_id, agent, db)

    ticket.assigned_agent_id = agent.id if payload.claim else None
    db.commit()
    return _read_ticket_with_computed_fields(ticket, db)


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageRead])
def list_ticket_messages(
    ticket_id: int, agent: Agent = Depends(require_agent), db: Session = Depends(get_db)
) -> list[TicketMessage]:
    """İlk AI destekli yanıttan sonraki takip mesajlarını en eskiden en
    yeniye listeler (bkz. CLAUDE.md 'özgün 10 özellik' listesi #6)."""
    _get_own_ticket(ticket_id, agent, db)
    stmt = (
        select(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/{ticket_id}/messages", response_model=TicketMessageRead)
def create_ticket_message(
    ticket_id: int,
    payload: TicketMessageCreate,
    agent: Agent = Depends(require_agent),
    db: Session = Depends(get_db),
) -> TicketMessage:
    """Bir temsilcinin talebe doğrudan (AI taslağı olmadan) yazdığı bir takip
    mesajı — ilk yanıt hâlâ mutlaka onay sürecinden geçer, bu sadece devam
    eden bir konuşmadaki serbest metin mesajdır."""
    ticket = _get_own_ticket(ticket_id, agent, db)
    message = TicketMessage(ticket_id=ticket.id, sender_type="agent", sender_name=agent.name, body=payload.body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

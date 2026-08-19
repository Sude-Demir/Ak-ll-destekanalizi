"""Kimlik doğrulaması GEREKTİRMEYEN, herkese açık uç noktalar.

Gerçek müşteriler bir Clerk hesabına sahip değildir — bu router bilinçli
olarak `require_auth`/`verify_webhook_auth` kullanmaz, tıpkı bir şirketin
herkese açık "Bize Ulaşın" formu gibi. Her şirketin kendi `slug`'ı vardır
(bkz. app.models.company) — URL bu şekilde hangi şirkete yazıldığını
belirtir, herkese açık bir "şirket seç" listesi YOKTUR (bkz. plan Context).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Company, Ticket
from app.schemas import CompanyRead, PublicTicketCreate, TicketRead

router = APIRouter(prefix="/public", tags=["public"])


def _get_company_by_slug(slug: str, db: Session) -> Company:
    company = db.execute(select(Company).filter(Company.slug == slug)).scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı")
    return company


@router.get("/companies/{slug}", response_model=CompanyRead)
def get_company(slug: str, db: Session = Depends(get_db)) -> Company:
    """Talep formunun/portalın başlığında şirket adını gösterebilmek için
    (bkz. frontend /support/[slug])."""
    return _get_company_by_slug(slug, db)


@router.post("/companies/{slug}/tickets", response_model=TicketRead)
def submit_support_request(slug: str, payload: PublicTicketCreate, db: Session = Depends(get_db)) -> Ticket:
    """Müşterinin, bir şirketin kendi herkese açık destek formu üzerinden
    gönderdiği talebi kaydeder (bkz. frontend /support/[slug] sayfası).
    """
    company = _get_company_by_slug(slug, db)
    ticket = Ticket(
        company_id=company.id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        body=payload.body,
        channel="form",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

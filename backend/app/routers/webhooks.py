"""Dış servislerden (Postmark) gelen webhook isteklerini karşılar.

Bu router bilinçli olarak `require_auth` (Clerk) KULLANMAZ — istekler bir
temsilciden değil, Postmark'ın sunucularından gelir. Bunun yerine HTTP Basic
Auth ile korunur (bkz. verify_webhook_auth); kimlik bilgileri webhook URL'sine
gömülür: https://<user>:<pass>@.../webhooks/inbound-email
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import verify_webhook_auth
from app.db.database import get_db
from app.models import Company, Ticket
from app.schemas import InboundEmailPayload, TicketRead

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/inbound-email",
    response_model=TicketRead,
    dependencies=[Depends(verify_webhook_auth)],
)
def receive_inbound_email(payload: InboundEmailPayload, db: Session = Depends(get_db)) -> Ticket:
    """Postmark'tan gelen bir e-postayı yeni bir destek talebine (ticket) çevirir.

    Hangi şirkete ait olduğu `MailboxHash`'ten (Postmark'ın "+slug" adresleme
    etiketi — bkz. app.schemas.InboundEmailPayload) çözülür; şirketin gelen
    e-posta adresi `adres+{slug}@inbound.postmarkapp.com` biçiminde kurulmalı.

    Bu uç nokta MÜŞTERİYE hiçbir şey göndermez — sadece bir talep kaydı
    oluşturur; yanıt üretimi ve onayı ayrı, mevcut akıştır (bkz. CLAUDE.md
    "İnsan onaylı akış").
    """
    company = db.execute(select(Company).filter(Company.slug == payload.MailboxHash)).scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=400, detail="E-posta adresinden şirket çözülemedi")

    ticket = Ticket(
        company_id=company.id,
        customer_name=payload.FromFull.Name or payload.From,
        customer_email=payload.FromFull.Email,
        subject=payload.Subject or "(konu belirtilmemiş)",
        body=payload.TextBody,
        channel="email",
        is_lead=False,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

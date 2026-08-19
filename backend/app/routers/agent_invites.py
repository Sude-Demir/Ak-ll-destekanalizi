import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_agent, require_auth
from app.db.database import get_db
from app.models import Agent, AgentInvite
from app.schemas import AgentInviteCreate, AgentInviteRead
from app.services.clerk_users import fetch_user_profile

router = APIRouter(prefix="/agent-invites", tags=["agent-invites"])

INVITE_VALID_DAYS = 7


@router.post("", response_model=AgentInviteRead, dependencies=[Depends(require_agent)])
def create_invite(
    payload: AgentInviteCreate,
    clerk_user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
) -> AgentInvite:
    """Bir temsilci, `scripts/add_agent.py`'yi elle çalıştırmak yerine
    panelden yeni bir temsilci daveti oluşturur. Gerçek e-posta gönderimi
    yok (bkz. plan) — linki temsilci kendisi kopyalayıp paylaşır."""
    now = datetime.datetime.now(datetime.timezone.utc)
    invite = AgentInvite(
        token=secrets.token_urlsafe(32),
        email=payload.email,
        name=payload.name,
        invited_by=clerk_user_id,
        expires_at=now + datetime.timedelta(days=INVITE_VALID_DAYS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("", response_model=list[AgentInviteRead], dependencies=[Depends(require_agent)])
def list_invites(db: Session = Depends(get_db)) -> list[AgentInvite]:
    stmt = select(AgentInvite).order_by(AgentInvite.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.get("/{token}", response_model=AgentInviteRead)
def preview_invite(token: str, db: Session = Depends(get_db)) -> AgentInvite:
    """Kimlik doğrulaması istemez — davet linkine tıklayan kişi giriş
    yapmadan önce 'kim davet etti, hangi e-posta için' bilgisini görebilsin
    diye. Bu uç nokta hiçbir şeyi KABUL ETMEZ (bkz. POST .../accept) —
    e-posta istemcilerinin linki otomatik önizlemesi (prefetch) yanlışlıkla
    bir daveti tüketmesin diye kasıtlı olarak yan etkisiz tutuldu."""
    invite = db.execute(select(AgentInvite).filter(AgentInvite.token == token)).scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="Davet bulunamadı")
    return invite


@router.post("/{token}/accept", response_model=AgentInviteRead)
def accept_invite(
    token: str, clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> AgentInvite:
    """Daveti kabul edip giriş yapan kişiyi `agents` tablosuna ekler.

    Linkin kendisi tek başına yeterli değil: kabul eden kişinin Clerk
    hesabındaki gerçek e-postası davetteki e-postayla eşleşmiyorsa reddedilir
    — aksi halde linki ele geçiren rastgele biri temsilci olabilirdi.
    """
    invite = db.execute(select(AgentInvite).filter(AgentInvite.token == token)).scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="Davet bulunamadı")

    now = datetime.datetime.now(datetime.timezone.utc)
    if invite.expires_at < now:
        raise HTTPException(status_code=410, detail="Bu davetin süresi dolmuş")
    if invite.accepted_at is not None:
        raise HTTPException(status_code=400, detail="Bu davet zaten kullanılmış")

    name, email = fetch_user_profile(clerk_user_id)
    if email.strip().lower() != invite.email.strip().lower():
        raise HTTPException(
            status_code=403,
            detail=f"Bu davet {invite.email} için gönderildi, farklı bir hesapla giriş yaptınız",
        )

    existing_agent = db.execute(
        select(Agent).filter(Agent.clerk_user_id == clerk_user_id)
    ).scalar_one_or_none()
    if existing_agent is None:
        db.add(Agent(clerk_user_id=clerk_user_id, name=invite.name or name))

    invite.accepted_at = now
    db.commit()
    db.refresh(invite)
    return invite

"""Bu API'ye kimlerin erişebileceğini kontrol eden FastAPI bağımlılıkları.

Üç farklı doğrulama mekanizması var, çünkü isteklerin kaynağı ve yetki
seviyesi farklı:
- `require_auth`: giriş yapmış herkes (frontend), Clerk oturumuyla — hem
  temsilciler hem müşteriler için ortak zemin (bkz. app.routers.me).
- `require_agent`: sadece temsilciler — `agents` tablosunda kaydı olmayan
  bir müşteri, talep listesine veya AI taslaklarına erişemesin diye.
- `verify_webhook_auth`: dış servisler (Postmark), HTTP Basic Auth ile.
"""

import secrets

from clerk_backend_api import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.agent import Agent

_basic_auth = HTTPBasic()


def require_auth(request: Request) -> str:
    """Authorization header'ındaki Clerk oturum token'ını doğrular (frontend,
    `Authorization: Bearer <session_token>` header'ıyla istek atıyor — bkz.
    frontend/lib/api.ts) ve oturumu açan kullanıcının id'sini (`sub` claim'i)
    döner. Token yoksa/geçersizse 401 fırlatır.

    Bu, frontend'deki `/dashboard` giriş korumasının backend tarafındaki
    karşılığıdır: frontend atlanıp doğrudan bu API'ye istek atılırsa da aynı
    koruma geçerli olsun diye.
    """
    request_state = authenticate_request(
        request,
        AuthenticateRequestOptions(secret_key=settings.clerk_secret_key),
    )
    if not request_state.is_signed_in or request_state.payload is None:
        raise HTTPException(status_code=401, detail="Kimlik doğrulanamadı")
    return request_state.payload["sub"]


def require_agent(
    clerk_user_id: str = Depends(require_auth), db: Session = Depends(get_db)
) -> Agent:
    """`require_auth`'un üstüne kurulu: giriş yapan kişi ayrıca `agents`
    tablosunda kayıtlı değilse 403 fırlatır. Talep listesi ve AI taslakları
    gibi müşterinin görmemesi gereken uç noktalarda kullanılır (bkz.
    app.routers.tickets, app.routers.drafts).
    """
    agent = db.execute(select(Agent).filter(Agent.clerk_user_id == clerk_user_id)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=403, detail="Bu işlem için temsilci yetkisi gerekiyor")
    return agent


def verify_webhook_auth(credentials: HTTPBasicCredentials = Depends(_basic_auth)) -> None:
    """Postmark'ın gelen e-posta webhook'unu doğrular. Kimlik bilgileri
    webhook URL'sine gömülür (https://<user>:<pass>@.../webhooks/...),
    Postmark'ın kendisi bunu her istekte Basic Auth header'ı olarak gönderir.

    `secrets.compare_digest` kullanılır — normal `==` zamanlama saldırılarına
    (timing attack) açık olurdu.
    """
    valid_username = secrets.compare_digest(credentials.username, settings.webhook_username or "")
    valid_password = secrets.compare_digest(credentials.password, settings.webhook_password or "")
    if not (valid_username and valid_password):
        raise HTTPException(status_code=401, detail="Yetkisiz webhook isteği")

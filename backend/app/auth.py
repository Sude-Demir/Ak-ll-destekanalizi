"""Bu API'ye kimlerin erişebileceğini kontrol eden FastAPI bağımlılıkları.

İki farklı doğrulama mekanizması var, çünkü isteklerin kaynağı farklı:
- `require_auth`: temsilciler (frontend), Clerk oturumuyla.
- `verify_webhook_auth`: dış servisler (Postmark), HTTP Basic Auth ile.
"""

import secrets

from clerk_backend_api import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

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

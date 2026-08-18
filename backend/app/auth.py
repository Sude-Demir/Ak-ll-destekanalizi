"""FastAPI bağımlılığı: gelen isteğin Clerk oturumuyla kimliği doğrulanmış
olduğunu kontrol eder (frontend, `Authorization: Bearer <session_token>`
header'ıyla istek atıyor — bkz. frontend/lib/api.ts).

Bu, frontend'deki `/dashboard` giriş korumasının backend tarafındaki
karşılığıdır: frontend atlanıp doğrudan bu API'ye istek atılırsa da aynı
koruma geçerli olsun diye.
"""

from clerk_backend_api import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import HTTPException, Request

from app.config import settings


def require_auth(request: Request) -> str:
    """Authorization header'ındaki Clerk oturum token'ını doğrular ve oturumu
    açan kullanıcının id'sini (`sub` claim'i) döner. Token yoksa/geçersizse
    401 fırlatır."""
    request_state = authenticate_request(
        request,
        AuthenticateRequestOptions(secret_key=settings.clerk_secret_key),
    )
    if not request_state.is_signed_in or request_state.payload is None:
        raise HTTPException(status_code=401, detail="Kimlik doğrulanamadı")
    return request_state.payload["sub"]

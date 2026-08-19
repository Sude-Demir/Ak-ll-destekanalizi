"""Clerk'ten giriş yapan kullanıcının profil bilgisini okur.

Müşteri portalında (bkz. app.routers.me) ad/e-posta talep gövdesinde
istenmez — biri talep açarken başkasının adını/e-postasını yazabilirdi. Bu
bilgiler doğrudan Clerk oturumunun sahibinden okunur, taklit edilemez.
"""

from clerk_backend_api import Clerk

from app.config import settings


def fetch_user_profile(clerk_user_id: str) -> tuple[str, str]:
    """Verilen Clerk kullanıcı kimliği için (ad, e-posta) döner."""
    with Clerk(bearer_auth=settings.clerk_secret_key) as clerk:
        user = clerk.users.get(user_id=clerk_user_id)

    name = " ".join(part for part in (user.first_name, user.last_name) if part)
    if not name:
        name = "İsimsiz Kullanıcı"

    primary_email = next(
        (e.email_address for e in user.email_addresses if e.id == user.primary_email_address_id),
        None,
    )
    email = primary_email or (user.email_addresses[0].email_address if user.email_addresses else "")

    return name, email

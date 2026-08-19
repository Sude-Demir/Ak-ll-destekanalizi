import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Company(Base):
    """Bir kiracı (tenant) — kendi bilgi tabanı, kendi temsilcileri, kendi
    talepleri olan bir şirket. `slug`, hem herkese açık talep formunun
    URL'sinde (`/support/{slug}`) hem gelen e-posta adresinde
    (`adres+{slug}@...`) şirketi ayırt etmek için kullanılır — bkz.
    app.routers.public, app.routers.webhooks."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

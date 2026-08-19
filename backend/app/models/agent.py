import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Agent(Base):
    """Destek ekibinin bir üyesi. Bir Clerk kullanıcısının bu tabloda kaydı
    varsa temsilci sayılır (bkz. app.auth.require_agent); yoksa müşteri
    sayılır ve giriş sonrası kendi talep portalına yönlendirilir.

    `clerk_user_id` global olarak unique — bir kişi tek şirkette temsilci
    olabilir (bilinçli basitleştirme, bkz. plan "Kapsam dışı")."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

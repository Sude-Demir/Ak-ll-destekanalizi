import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AgentInvite(Base):
    """Bir temsilcinin başka birini ekibe davet etmesi (bkz.
    app.routers.agent_invites). Kabul edilince `agents` tablosuna bir satır
    eklenir — bu, `scripts/add_agent.py`'nin self-servis karşılığıdır."""

    __tablename__ = "agent_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    email: Mapped[str] = mapped_column(String(255))
    # Davet ederken önerilen görünen ad; boşsa kabul anında Clerk profilinden okunur.
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invited_by: Mapped[str] = mapped_column(String(255))
    accepted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

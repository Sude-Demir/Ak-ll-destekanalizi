import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class EvalExample(Base):
    """Elle işaretlenmiş bir eval örneği: bir talep için "doğru cevap ne
    olmalıydı" bilgisini tutar. Prompt/model değişikliklerini gerçek müşteri
    verisine uygulamadan önce bunlara karşı test etmek için kullanılır
    (bkz. CLAUDE.md "Kesinlikle Yapılmaması Gerekenler")."""

    __tablename__ = "eval_examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    expected_category: Mapped[str] = mapped_column(String(50))
    # "Doğru" tek bir cevap metni yerine, taslağın içermesi gereken ana
    # noktaların özeti — LLM çıktısıyla birebir metin eşleşmesi aranmaz.
    expected_answer_summary: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

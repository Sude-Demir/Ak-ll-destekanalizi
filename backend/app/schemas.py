import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.services.confidence import needs_escalation


class TicketRead(BaseModel):
    """API üzerinden dışa dönen ticket temsili (giriş/çıkış doğrulaması)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_email: str
    subject: str
    body: str
    channel: str
    category: str | None
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # Onaylanmış/düzenlenmiş bir taslağı var mı (bkz. app.models.draft_response
    # ANSWERED_DRAFT_STATUSES). Varsayılan False — çünkü bu alan sadece
    # app.routers.tickets tarafından hesaplanıp dolduruluyor; TicketRead'i
    # doğrudan bir Ticket ORM nesnesinden üreten diğer uç noktalarda
    # (public.py, webhooks.py — yeni oluşturulan bir talep, henüz taslaksız)
    # doğru varsayılan zaten budur.
    is_answered: bool = False


class DraftResponseRead(BaseModel):
    """API üzerinden dışa dönen taslak yanıt temsili."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    draft_text: str
    retrieved_context: list[dict]
    confidence_score: float | None
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @computed_field
    @property
    def needs_escalation(self) -> bool:
        """Güven skoru eşiğin altındaysa true döner (bkz.
        app.services.confidence.ESCALATION_THRESHOLD). Skor henüz yoksa
        (confidence_score=None) temkinli davranıp true döner."""
        return self.confidence_score is None or needs_escalation(self.confidence_score)


class DraftStatusUpdate(BaseModel):
    """Bir temsilcinin taslak üzerindeki kararı: onayla, düzenleyerek onayla
    veya reddet (bkz. CLAUDE.md "İnsan onaylı akış")."""

    status: Literal["approved", "edited", "rejected"]
    # Sadece status="edited" iken kullanılır: temsilcinin düzenlediği son metin.
    draft_text: str | None = None


class CompanyRead(BaseModel):
    """Herkese açık, minimal şirket temsili — talep formunun/portalın
    başlığında ("X'e Ulaşın") göstermek için (bkz. app.routers.public)."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class PublicTicketCreate(BaseModel):
    """Herkese açık destek formundan (bkz. app.routers.public) gelen talep
    verisi. Gerçek müşteriler bir Clerk hesabına sahip değildir, bu yüzden bu
    şema hiçbir kimlik doğrulaması gerektirmeyen bir uç noktada kullanılır."""

    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)


class PostmarkFromFull(BaseModel):
    """Postmark'ın inbound webhook payload'undaki gönderen bilgisi."""

    model_config = ConfigDict(extra="ignore")

    Email: str
    Name: str = ""


class MeRead(BaseModel):
    """Giriş yapan kullanıcının kendi profili — frontend'in `/dashboard` mı
    `/portal` mı göstereceğine karar verdiği yer (bkz. app.routers.me)."""

    clerk_user_id: str
    is_agent: bool
    name: str
    # Temsilciyse hangi şirkete ait olduğu; müşteride None.
    company_name: str | None = None


class MyTicketCreate(BaseModel):
    """Giriş yapmış bir müşterinin kendi portalından açtığı talep. Ad/e-posta
    burada istenmez — Clerk oturumundan okunur (bkz.
    app.services.clerk_users). `company_slug`, talebin hangi şirkete
    gideceğini belirtir (bkz. app/portal/new/[slug])."""

    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    company_slug: str


class MyTicketRead(BaseModel):
    """Müşterinin kendi talebi için gördüğü, indirgenmiş temsil. Taslağın
    dayandığı SSS kaynakları ve güven skoru gibi iç bilgiler burada YOK —
    sadece onaylanmış/düzenlenmiş bir taslak varsa `answer` alanında
    görünür (bkz. CLAUDE.md "İnsan onaylı akış"). Müşteri artık birden
    fazla şirkete talep açabildiği için hangi şirkete ait olduğu da döner."""

    id: int
    subject: str
    body: str
    created_at: datetime.datetime
    answer: str | None
    company_name: str
    company_slug: str


class AgentInviteCreate(BaseModel):
    """Bir temsilcinin başka birini ekibe davet etmek için gönderdiği bilgi
    (bkz. app.routers.agent_invites)."""

    email: EmailStr
    name: str | None = Field(default=None, max_length=255)


class AgentInviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    email: str
    name: str | None
    invited_by: str
    expires_at: datetime.datetime
    created_at: datetime.datetime
    accepted_at: datetime.datetime | None

    @computed_field
    @property
    def status(self) -> Literal["pending", "accepted", "expired"]:
        if self.accepted_at is not None:
            return "accepted"
        now = datetime.datetime.now(datetime.timezone.utc)
        if self.expires_at < now:
            return "expired"
        return "pending"


class InboundEmailPayload(BaseModel):
    """Postmark'ın gelen e-posta webhook'unun gönderdiği JSON — sadece bizim
    kullandığımız alanlar tanımlı, geri kalanı yok sayılır (Postmark onlarca
    ek alan gönderir: Attachments, Headers, MessageID vb.).
    https://postmarkapp.com/developer/webhooks/inbound-webhook
    """

    model_config = ConfigDict(extra="ignore")

    From: str
    FromFull: PostmarkFromFull
    Subject: str = ""
    TextBody: str = ""
    # Postmark'ın "+etiket" adreslemesindeki etiket kısmı — bir şirketin
    # gelen e-posta adresi `adres+{slug}@inbound.postmarkapp.com` biçiminde
    # kurulursa, Postmark bu alana şirketin slug'ını koyar (bkz.
    # app.routers.webhooks receive_inbound_email).
    MailboxHash: str = ""

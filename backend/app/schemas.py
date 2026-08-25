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
    is_lead: bool = False
    is_urgent: bool = False
    status: str
    # Talebi üstlenen temsilci — kimse üstlenmediyse ikisi de None.
    # assigned_agent_id gerçek bir sütun (Ticket ORM nesnesinden otomatik
    # gelir); assigned_agent_name ise is_answered gibi ayrıca çözülüp
    # app.routers.tickets tarafından doldurulur.
    assigned_agent_id: int | None = None
    assigned_agent_name: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # Onaylanmış/düzenlenmiş bir taslağı var mı (bkz. app.models.draft_response
    # ANSWERED_DRAFT_STATUSES). Varsayılan False — çünkü bu alan sadece
    # app.routers.tickets tarafından hesaplanıp dolduruluyor; TicketRead'i
    # doğrudan bir Ticket ORM nesnesinden üreten diğer uç noktalarda
    # (public.py, webhooks.py — yeni oluşturulan bir talep, henüz taslaksız)
    # doğru varsayılan zaten budur.
    is_answered: bool = False
    # Bu talebin en yeni "pending" durumdaki taslağının id'si — yoksa None
    # (bkz. app.routers.drafts bulk_approve_tickets). Varsayılan None — diğer
    # is_answered gibi sadece app.routers.tickets tarafından doldurulur.
    pending_draft_id: int | None = None


class DraftResponseRead(BaseModel):
    """API üzerinden dışa dönen taslak yanıt temsili."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    draft_text: str
    # AI'nin ilk ürettiği, hiç değişmeyen metin — draft_text bir temsilci
    # tarafından düzenlenince ondan ayrışır (bkz. app.models.draft_response).
    ai_original_text: str
    retrieved_context: list[dict]
    confidence_score: float | None
    used_customer_history: bool = False
    status: str
    # Müşterinin portalda bu yanıta verdiği hızlı tepki — bkz. MyTicketRead.reaction
    # ve app.routers.me update_ticket_reaction. Temsilci tarafında da görünür
    # olsun diye burada da dışa açılıyor (izlenebilirlik).
    customer_reaction: str | None = None
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


class TicketMessageRead(BaseModel):
    """İlk AI destekli yanıttan sonraki bir takip mesajı (bkz.
    app.models.ticket_message)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    sender_type: Literal["customer", "agent"]
    sender_name: str
    body: str
    created_at: datetime.datetime


class TicketMessageCreate(BaseModel):
    body: str = Field(min_length=1)


class TicketAssignmentUpdate(BaseModel):
    """Bir temsilcinin talebi üstlenmesi (`claim=true`, atama ARAYAN
    temsilciye geçer — başkasına atanmış olsa bile devralma serbest, küçük
    bir ekipte bu yeterli) ya da bırakması (`claim=false`)."""

    claim: bool


class KbSuggestionRead(BaseModel):
    """API üzerinden dışa dönen SSS (FAQ) önerisi temsili (bkz.
    app.services.kb_suggestion_generation)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    question: str
    answer: str
    category: str
    intent: str
    status: str
    kb_chunk_id: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class KbSuggestionStatusUpdate(BaseModel):
    """Bir temsilcinin SSS önerisi üzerindeki kararı: onayla (gerçek bir SSS
    kaydına dönüştür) veya reddet. Onaylamadan önce soru/cevap düzenlenebilir
    — bkz. DraftStatusUpdate ile aynı desen."""

    status: Literal["approved", "rejected"]
    question: str | None = None
    answer: str | None = None


class TicketListRead(BaseModel):
    """`GET /tickets`'in tam yanıtı — sadece o sayfadaki talepler (`items`)
    değil, aramadan/kategori filtresinden BAĞIMSIZ şirket geneli özet de
    içerir. Bu özet, TicketStats/CategoryDistribution/CategoryFilterBar'ın
    her zaman "şirketin tamamı" üzerinden doğru sayı göstermesi için var —
    sayfalama eklenince `items` artık tüm talepleri temsil etmiyor."""

    items: list[TicketRead]
    total: int  # q/category filtresi uygulanmış toplam (sayfalama için)
    page: int
    page_size: int
    overall_total: int
    open_count: int
    classified_count: int
    resolved_count: int
    category_counts: dict[str, int]


class BulkApproveRequest(BaseModel):
    ticket_ids: list[int]


class BulkApproveResult(BaseModel):
    approved: list[int]
    skipped: list[int]


class BulkGenerateResult(BaseModel):
    created: list[int]
    skipped: list[int]
    # Gerçek bir LLM çağrısı gerektirdiği için (bkz. app.routers.drafts
    # bulk_generate_drafts) — kota/ağ hatası olan talepler burada, işlem
    # durmadan sıradaki talebe devam edilir.
    failed: list[int]


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
    # Müşterinin bu yanıta verdiği hızlı tepki — yanıt yoksa (answer=None)
    # ya da henüz tepki verilmediyse None.
    reaction: str | None
    company_name: str
    company_slug: str


class TicketReactionUpdate(BaseModel):
    """Müşterinin portaldaki yanıta verdiği hızlı 👍/👎 tepkisi. `None`
    göndermek mevcut tepkiyi temizler (aynı butona tekrar basmak gibi)."""

    reaction: Literal["up", "down"] | None


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


class TicketTotals(BaseModel):
    """Bir şirketin toplam talep hacmi, kaçının cevaplandığı ve kaçının hiç
    taslak üretilmeden beklediği (bkz. app.routers.analytics)."""

    total: int
    answered: int
    without_draft: int


class DraftTotals(BaseModel):
    """Bir şirketin ürettiği taslakların durum dağılımı ve güven skoru özeti
    (bkz. app.routers.analytics)."""

    total: int
    pending: int
    approved: int
    edited: int
    rejected: int
    average_confidence: float | None
    escalated: int

    @computed_field
    @property
    def approval_rate(self) -> float | None:
        """Karara bağlanmış (pending olmayan) taslaklar içinde onaylanma
        oranı. Henüz hiçbir taslak karara bağlanmadıysa None döner —
        payda 0 olduğunda oranı 0 göstermek yanıltıcı olurdu."""
        decided = self.approved + self.edited + self.rejected
        return None if decided == 0 else (self.approved + self.edited) / decided


class DraftTrendPoint(DraftTotals):
    """DraftTotals'ın günlük hâli — bir günde üretilen taslakların durum
    dağılımı, ortalama güven skoru ve (miras alınan) onay oranı. Zaman
    içindeki AI performans trendini göstermek için (bkz. app.routers.analytics,
    CLAUDE.md 'özgün 10 özellik' listesi #9 — 'canlı bir eval' gibi çalışır)."""

    date: datetime.date


class DailyTicketCount(BaseModel):
    """Bir günde gelen talep sayısı (bkz. app.routers.analytics — hacim
    grafiği)."""

    date: datetime.date
    count: int


class NotificationRead(BaseModel):
    """Bir lead/acil talep tespiti in-app bildirimi (bkz. app.models.notification,
    CLAUDE.md 'özgün 10 özellik' listesi #10). `ticket_subject` gerçek bir
    Notification sütunu değil — TicketRead.assigned_agent_name ile aynı
    desende, app.routers.notifications tarafından bir join'le doldurulur."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    type: Literal["lead", "urgent"]
    ticket_subject: str = ""
    created_at: datetime.datetime
    read_at: datetime.datetime | None


class KnowledgeGapItem(BaseModel):
    """Bir kategoride AI'nin ne sıklıkla düşük güvenle/eskalasyona düşerek
    taslak ürettiğini gösterir — şirketin SSS'inde muhtemelen eksik olan bir
    konuyu işaret eder (bkz. app.routers.analytics _knowledge_gaps).
    `sample_subjects`, o kategoride eskale olmuş en yeni birkaç talebin
    başlığıdır — rapor soyut bir sayı değil, somut örneklerle gelsin diye."""

    category: str
    escalated_count: int
    total_count: int
    sample_subjects: list[str]


class AnalyticsRead(BaseModel):
    """Bir temsilcinin şirketi için toplu performans özeti — kaç talep
    geldi, AI taslakları ne oranda onaylandı, sistem nerede zorlanıyor
    (bkz. app.routers.analytics)."""

    tickets: TicketTotals
    drafts: DraftTotals
    daily_ticket_counts: list[DailyTicketCount]
    draft_trend: list[DraftTrendPoint]


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

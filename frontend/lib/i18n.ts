// Kütüphanesiz, ince bir i18n çözümü (bkz. CLAUDE.md "ince soyutlama, ağır
// framework değil"). Proje şu an locale-bazlı URL routing kullanmıyor
// (/tr/... /en/... yok) — dil tercihi bir cookie'de tutuluyor, bu dosya
// hem server hem client component'lerden import edilebilir (next/headers
// GİBİ server-only bir şey İÇERMEZ — o `lib/i18n-server.ts`'te).

export type Locale = "tr" | "en";

export const DEFAULT_LOCALE: Locale = "tr";
export const LOCALE_COOKIE = "locale";

const tr = {
  // Ortak
  "common.signIn": "Giriş Yap",

  // Karşılama ekranı (app/page.tsx)
  "welcome.subtitleSignedOut": "Destek taleplerini yönetmek veya yeni bir talep göndermek için giriş yapın.",
  "welcome.greeting": "Hoş geldin, {name}.",
  "welcome.subtitleAgent": "Gelen destek taleplerini görüntülemeye devam et.",
  "welcome.subtitleCustomer": "Taleplerini görüntüle veya yeni bir talep gönder.",
  "welcome.goToDashboard": "Panele Git",
  "welcome.goToPortal": "Taleplerime Git",

  // Dashboard (talep listesi)
  "dashboard.title": "Destek Talepleri",
  "dashboard.subtitle": "Bir talebe tıklayarak detayını görüntüleyebilir ve AI destekli yanıt taslağı oluşturabilirsin.",
  "dashboard.loadError": "Destek talepleri yüklenemedi. Backend'in (http://localhost:8000) çalıştığından emin olun.",
  "dashboard.team": "Ekip",
  "dashboard.emptyForCategory": "Bu kategoride ({category}) talep yok.",
  "dashboard.loadingAriaLabel": "Destek talepleri yükleniyor",

  // Talep tablosu (TicketsTable)
  "ticketsTable.subject": "Talep",
  "ticketsTable.category": "Kategori",
  "ticketsTable.channel": "Kanal",
  "ticketsTable.answer": "Cevap",
  "ticketsTable.createdAt": "Oluşturulma",
  "ticketsTable.ariaLabel": "Destek talepleri",
  "ticketsTable.empty": "Henüz destek talebi bulunmuyor.",
  "ticketsTable.answered": "Cevaplandı",
  "ticketsTable.unanswered": "Cevaplanmadı",
  "ticketStatus.open": "Açık",
  "ticketStatus.pending": "Beklemede",
  "ticketStatus.closed": "Kapalı",

  // Talep detayı (dashboard/tickets/[id])
  "ticketDetail.back": "← Tüm taleplere dön",
  "ticketDetail.channel": "Kanal",
  "ticketDetail.category": "Kategori",
  "ticketDetail.unclassified": "Henüz sınıflandırılmadı",
  "ticketDetail.createdAt": "Oluşturulma",

  // Taslak paneli (DraftPanel)
  "draftPanel.statusPending": "Onay bekliyor",
  "draftPanel.statusApproved": "Onaylandı",
  "draftPanel.statusEdited": "Düzenlendi",
  "draftPanel.statusRejected": "Reddedildi",
  "draftPanel.saveError": "İşlem kaydedilemedi. Backend'in çalıştığından emin olun.",
  "draftPanel.needsAttention": "Dikkatli incele",
  "draftPanel.confidence": "Güven",
  "draftPanel.sourcesHeading": "Bu taslak şu SSS içeriklerine dayanıyor",
  "draftPanel.saving": "Kaydediliyor…",
  "draftPanel.save": "Kaydet",
  "draftPanel.cancel": "İptal",
  "draftPanel.approving": "Onaylanıyor…",
  "draftPanel.approve": "Onayla",
  "draftPanel.edit": "Düzenle",
  "draftPanel.rejecting": "Reddediliyor…",
  "draftPanel.reject": "Reddet",
  "draftPanel.generateError": "Taslak oluşturulamadı. Backend'in çalıştığından ve Gemini API anahtarının geçerli olduğundan emin olun.",
  "draftPanel.heading": "Yanıt Taslakları",
  "draftPanel.generating": "Oluşturuluyor…",
  "draftPanel.generate": "Taslak Oluştur",
  "draftPanel.empty": "Bu talep için henüz bir taslak yok. Oluşturmak için yukarıdaki butona tıkla.",

  // Kategori bileşenleri
  "categoryFilter.ariaLabel": "Kategoriye göre filtrele",
  "categoryFilter.all": "Tümü",
  "categoryDistribution.heading": "Kategori Dağılımı",
  "categoryDistribution.ariaLabel": "Kategori dağılımı lejantı",
  "categoryDistribution.other": "Diğer",
  "category.unclassified": "Sınıflandırılmadı",

  // İstatistikler (TicketStats)
  "ticketStats.total": "toplam talep",
  "ticketStats.open": "açık",
  "ticketStats.classified": "sınıflandırıldı",
  "ticketStats.resolved": "çözüldü",

  // Ekip / davet
  "team.title": "Ekip",
  "team.subtitle": "Yeni bir temsilci davet edin. Oluşturulan link 7 gün geçerlidir — kopyalayıp paylaşmanız yeterli.",
  "team.loadError": "Davetler yüklenemedi. Lütfen sayfayı yenileyin.",
  "inviteForm.email": "E-posta",
  "inviteForm.name": "Ad Soyad",
  "inviteForm.optional": "(opsiyonel)",
  "inviteForm.creating": "Oluşturuluyor…",
  "inviteForm.create": "Davet Oluştur",
  "inviteForm.error": "Davet oluşturulamadı. Lütfen tekrar deneyin.",
  "inviteList.empty": "Henüz bir davet oluşturulmadı.",
  "inviteList.pending": "Bekliyor",
  "inviteList.accepted": "Kabul edildi",
  "inviteList.expired": "Süresi doldu",
  "inviteList.validUntil": "{date} tarihine kadar geçerli",
  "inviteList.createdAt": "Oluşturulma: {date}",
  "copyLink.copy": "Kopyala",
  "copyLink.copied": "Kopyalandı",
  "inviteAccept.heading": "Akıllı Destek Ekibine Davet",
  "inviteAccept.pendingPrefix": "Bu davet",
  "inviteAccept.pendingSuffix": " adresi için gönderildi. Kabul etmek için bu e-postaya sahip hesabınla giriş yapmış olman gerekiyor.",
  "inviteAccept.accepted": "Bu davet zaten kabul edilmiş.",
  "inviteAccept.expired": "Bu davetin süresi dolmuş. Ekipten yeni bir davet istemen gerekiyor.",
  "acceptInvite.accepting": "Kabul ediliyor…",
  "acceptInvite.accept": "Daveti Kabul Et",
  "acceptInvite.genericError": "Davet kabul edilemedi.",

  // Müşteri portalı
  "portal.title": "Destek Taleplerim",
  "portal.subtitle": "Önceki taleplerinizin durumunu buradan görüntüleyebilirsiniz. Yeni bir talep göndermek için ilgili şirketin size verdiği bağlantıyı kullanın.",
  "portal.loadError": "Talepleriniz yüklenemedi. Lütfen sayfayı yenileyin.",
  "portalTicketDetail.back": "← Taleplerim",
  "portalTicketDetail.answerHeading": "Yanıtımız",
  "portalTicketDetail.pending": "Talebiniz inceleniyor. Destek ekibimiz en kısa sürede size dönüş yapacak.",
  "newTicket.heading": "{company} için yeni talep",
  "newTicket.back": "← Taleplerim",
  "newTicket.subject": "Konu",
  "newTicket.body": "Mesajınız",
  "newTicket.submitting": "Gönderiliyor…",
  "newTicket.submit": "Talebi Gönder",
  "newTicket.error": "Talebiniz gönderilemedi. Lütfen birkaç dakika sonra tekrar deneyin.",
  "myTickets.ariaLabel": "Taleplerim",
  "myTickets.empty": "Henüz bir talep göndermediniz.",
  "myTickets.answered": "Cevaplandı",
  "myTickets.pending": "İnceleniyor",

  // Herkese açık form (/support)
  "support.heading": "{company}'e Ulaşın",
  "support.subtitle": "Bir sorunuz veya sorununuz mu var? Aşağıdaki formu doldurun, destek ekibimiz size dönüş yapsın.",
  "support.name": "Ad Soyad",
  "support.email": "E-posta",
  "support.subject": "Konu",
  "support.body": "Mesajınız",
  "support.submitting": "Gönderiliyor…",
  "support.submit": "Talebi Gönder",
  "support.error": "Talebiniz gönderilemedi. Lütfen birkaç dakika sonra tekrar deneyin.",
  "support.successTitle": "Talebiniz alındı",
  "support.successBodyPrefix": "Talep numaranız #",
  "support.successBodySuffix": ". Ekibimiz en kısa sürede size dönüş yapacak.",

  // Sayfa meta (app/layout.tsx)
  "meta.description": "Müşteri destek taleplerini yöneten iç panel",
} as const;

const en: Record<keyof typeof tr, string> = {
  "common.signIn": "Sign In",

  "welcome.subtitleSignedOut": "Sign in to manage support tickets or submit a new one.",
  "welcome.greeting": "Welcome, {name}.",
  "welcome.subtitleAgent": "Continue viewing incoming support tickets.",
  "welcome.subtitleCustomer": "View your tickets or submit a new one.",
  "welcome.goToDashboard": "Go to Dashboard",
  "welcome.goToPortal": "Go to My Tickets",

  "dashboard.title": "Support Tickets",
  "dashboard.subtitle": "Click a ticket to view its details and generate an AI-assisted draft reply.",
  "dashboard.loadError": "Couldn't load support tickets. Make sure the backend (http://localhost:8000) is running.",
  "dashboard.team": "Team",
  "dashboard.emptyForCategory": "No tickets in this category ({category}).",
  "dashboard.loadingAriaLabel": "Loading support tickets",

  "ticketsTable.subject": "Ticket",
  "ticketsTable.category": "Category",
  "ticketsTable.channel": "Channel",
  "ticketsTable.answer": "Answer",
  "ticketsTable.createdAt": "Created",
  "ticketsTable.ariaLabel": "Support tickets",
  "ticketsTable.empty": "No support tickets yet.",
  "ticketsTable.answered": "Answered",
  "ticketsTable.unanswered": "Unanswered",
  "ticketStatus.open": "Open",
  "ticketStatus.pending": "Pending",
  "ticketStatus.closed": "Closed",

  "ticketDetail.back": "← Back to all tickets",
  "ticketDetail.channel": "Channel",
  "ticketDetail.category": "Category",
  "ticketDetail.unclassified": "Not classified yet",
  "ticketDetail.createdAt": "Created",

  "draftPanel.statusPending": "Pending approval",
  "draftPanel.statusApproved": "Approved",
  "draftPanel.statusEdited": "Edited",
  "draftPanel.statusRejected": "Rejected",
  "draftPanel.saveError": "Couldn't save. Make sure the backend is running.",
  "draftPanel.needsAttention": "Needs review",
  "draftPanel.confidence": "Confidence",
  "draftPanel.sourcesHeading": "This draft is based on the following FAQ content",
  "draftPanel.saving": "Saving…",
  "draftPanel.save": "Save",
  "draftPanel.cancel": "Cancel",
  "draftPanel.approving": "Approving…",
  "draftPanel.approve": "Approve",
  "draftPanel.edit": "Edit",
  "draftPanel.rejecting": "Rejecting…",
  "draftPanel.reject": "Reject",
  "draftPanel.generateError": "Couldn't generate a draft. Make sure the backend is running and the Gemini API key is valid.",
  "draftPanel.heading": "Response Drafts",
  "draftPanel.generating": "Generating…",
  "draftPanel.generate": "Generate Draft",
  "draftPanel.empty": "There's no draft for this ticket yet. Click the button above to create one.",

  "categoryFilter.ariaLabel": "Filter by category",
  "categoryFilter.all": "All",
  "categoryDistribution.heading": "Category Distribution",
  "categoryDistribution.ariaLabel": "Category distribution legend",
  "categoryDistribution.other": "Other",
  "category.unclassified": "Not classified",

  "ticketStats.total": "total tickets",
  "ticketStats.open": "open",
  "ticketStats.classified": "classified",
  "ticketStats.resolved": "resolved",

  "team.title": "Team",
  "team.subtitle": "Invite a new teammate. The link is valid for 7 days — just copy and share it.",
  "team.loadError": "Couldn't load invites. Please refresh the page.",
  "inviteForm.email": "Email",
  "inviteForm.name": "Full Name",
  "inviteForm.optional": "(optional)",
  "inviteForm.creating": "Creating…",
  "inviteForm.create": "Create Invite",
  "inviteForm.error": "Couldn't create the invite. Please try again.",
  "inviteList.empty": "No invites created yet.",
  "inviteList.pending": "Pending",
  "inviteList.accepted": "Accepted",
  "inviteList.expired": "Expired",
  "inviteList.validUntil": "Valid until {date}",
  "inviteList.createdAt": "Created: {date}",
  "copyLink.copy": "Copy",
  "copyLink.copied": "Copied",
  "inviteAccept.heading": "Invitation to the Akıllı Destek Team",
  "inviteAccept.pendingPrefix": "This invite was sent to",
  "inviteAccept.pendingSuffix": ". To accept it, you need to be signed in with the account that owns this email.",
  "inviteAccept.accepted": "This invite has already been accepted.",
  "inviteAccept.expired": "This invite has expired. You'll need to ask the team for a new one.",
  "acceptInvite.accepting": "Accepting…",
  "acceptInvite.accept": "Accept Invite",
  "acceptInvite.genericError": "Couldn't accept the invite.",

  "portal.title": "My Support Tickets",
  "portal.subtitle": "View the status of your previous tickets here. To submit a new one, use the link the company gave you.",
  "portal.loadError": "Couldn't load your tickets. Please refresh the page.",
  "portalTicketDetail.back": "← My Tickets",
  "portalTicketDetail.answerHeading": "Our Reply",
  "portalTicketDetail.pending": "Your ticket is being reviewed. Our support team will get back to you shortly.",
  "newTicket.heading": "New ticket for {company}",
  "newTicket.back": "← My Tickets",
  "newTicket.subject": "Subject",
  "newTicket.body": "Your message",
  "newTicket.submitting": "Sending…",
  "newTicket.submit": "Send Ticket",
  "newTicket.error": "Your ticket couldn't be sent. Please try again in a few minutes.",
  "myTickets.ariaLabel": "My Tickets",
  "myTickets.empty": "You haven't submitted any tickets yet.",
  "myTickets.answered": "Answered",
  "myTickets.pending": "Under review",

  "support.heading": "Contact {company}",
  "support.subtitle": "Have a question or an issue? Fill out the form below and our support team will get back to you.",
  "support.name": "Full Name",
  "support.email": "Email",
  "support.subject": "Subject",
  "support.body": "Your Message",
  "support.submitting": "Sending…",
  "support.submit": "Send Ticket",
  "support.error": "Your ticket couldn't be sent. Please try again in a few minutes.",
  "support.successTitle": "Your ticket has been received",
  "support.successBodyPrefix": "Your ticket number is #",
  "support.successBodySuffix": ". Our team will get back to you shortly.",

  "meta.description": "Internal panel for managing customer support tickets",
};

export const translations = { tr, en };
export type TranslationKey = keyof typeof tr;

/** `params` verilirse, metindeki `{ad}` yer tutucularını değiştirir (örn.
 * `t(locale, "welcome.greeting", { name: "Sude" })` → "Hoş geldin, Sude."). */
export function t(locale: Locale, key: TranslationKey, params?: Record<string, string | number>): string {
  let text = translations[locale][key];
  if (params) {
    for (const [param, value] of Object.entries(params)) {
      text = text.replace(`{${param}}`, String(value));
    }
  }
  return text;
}

export function formatDate(isoDate: string, locale: Locale): string {
  return new Date(isoDate).toLocaleString(locale === "tr" ? "tr-TR" : "en-US", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

/** `score`: 0-1 aralığında bir güven skoru. TR'de "%50", EN'de "50%" yazar. */
export function formatPercent(score: number, locale: Locale): string {
  const rounded = Math.round(score * 100);
  return locale === "tr" ? `%${rounded}` : `${rounded}%`;
}

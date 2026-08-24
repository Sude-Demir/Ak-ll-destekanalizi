export interface Ticket {
  id: number;
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
  channel: string;
  category: string | null;
  is_lead: boolean;
  is_urgent: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  is_answered: boolean;
  pending_draft_id: number | null;
  // Talebi üstlenen temsilci — kimse üstlenmediyse ikisi de null.
  assigned_agent_id: number | null;
  assigned_agent_name: string | null;
}

// GET /tickets'in tam yanıtı — `items` sadece o sayfadaki talepler, geri
// kalan alanlar arama/kategori filtresinden BAĞIMSIZ şirket geneli özet
// (bkz. backend/app/schemas.py TicketListRead).
export interface TicketList {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
  overall_total: number;
  open_count: number;
  classified_count: number;
  resolved_count: number;
  category_counts: Record<string, number>;
}

export interface FetchTicketsParams {
  q?: string;
  category?: string;
  customerEmail?: string;
  channel?: string;
  isAnswered?: boolean;
  isLead?: boolean;
  isUrgent?: boolean;
  sort?: "newest" | "oldest" | "priority";
  page?: number;
}

export interface RetrievedContextItem {
  chunk_id: number;
  category: string;
  intent: string;
  question: string;
  answer: string;
}

export interface DraftResponse {
  id: number;
  ticket_id: number;
  draft_text: string;
  // AI'nin ilk ürettiği, hiç değişmeyen metin — draft_text bir temsilci
  // tarafından düzenlenince ondan ayrışır (bkz. DraftPanel "orijinal öneri").
  ai_original_text: string;
  retrieved_context: RetrievedContextItem[];
  confidence_score: number | null;
  used_customer_history: boolean;
  status: string;
  // Müşterinin portalda bu yanıta verdiği hızlı tepki — bkz. MyTicket.reaction.
  customer_reaction: "up" | "down" | null;
  needs_escalation: boolean;
  created_at: string;
  updated_at: string;
}

export type DraftDecision = "approved" | "edited" | "rejected";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Backend'in her uç noktası bir Clerk oturumu istiyor (bkz. backend/app/auth.py) —
// `token`, çağıran taraf server component'te `auth()`'tan, client component'te
// `useAuth()`'tan alıp buraya iletir.
function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchTickets(token: string | null, params: FetchTicketsParams = {}): Promise<TicketList> {
  const searchParams = new URLSearchParams();
  if (params.q) searchParams.set("q", params.q);
  if (params.category) searchParams.set("category", params.category);
  if (params.customerEmail) searchParams.set("customer_email", params.customerEmail);
  if (params.channel) searchParams.set("channel", params.channel);
  if (params.isAnswered !== undefined) searchParams.set("is_answered", String(params.isAnswered));
  if (params.isLead !== undefined) searchParams.set("is_lead", String(params.isLead));
  if (params.isUrgent !== undefined) searchParams.set("is_urgent", String(params.isUrgent));
  if (params.sort) searchParams.set("sort", params.sort);
  if (params.page) searchParams.set("page", String(params.page));
  const qs = searchParams.toString();

  const res = await fetch(`${API_BASE_URL}/tickets${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Destek talepleri alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export interface BulkApproveResult {
  approved: number[];
  skipped: number[];
}

export async function bulkApproveTickets(ticketIds: number[], token: string | null): Promise<BulkApproveResult> {
  const res = await fetch(`${API_BASE_URL}/tickets/bulk-approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ ticket_ids: ticketIds }),
  });

  if (!res.ok) {
    throw new Error(`Taslaklar onaylanamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export interface BulkGenerateResult {
  created: number[];
  skipped: number[];
  failed: number[];
}

export async function bulkGenerateDrafts(ticketIds: number[], token: string | null): Promise<BulkGenerateResult> {
  const res = await fetch(`${API_BASE_URL}/tickets/bulk-generate-drafts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ ticket_ids: ticketIds }),
  });

  if (!res.ok) {
    throw new Error(`Taslaklar oluşturulamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function updateTicketAssignment(id: number, claim: boolean, token: string | null): Promise<Ticket> {
  const res = await fetch(`${API_BASE_URL}/tickets/${id}/assignment`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ claim }),
  });

  if (!res.ok) {
    throw new Error(`Talep ataması güncellenemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface TicketMessage {
  id: number;
  ticket_id: number;
  sender_type: "customer" | "agent";
  sender_name: string;
  body: string;
  created_at: string;
}

export async function fetchTicketMessages(ticketId: number, token: string | null): Promise<TicketMessage[]> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/messages`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Mesajlar alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function sendTicketMessage(ticketId: number, body: string, token: string | null): Promise<TicketMessage> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ body }),
  });

  if (!res.ok) {
    throw new Error(`Mesaj gönderilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchMyTicketMessages(ticketId: number, token: string | null): Promise<TicketMessage[]> {
  const res = await fetch(`${API_BASE_URL}/me/tickets/${ticketId}/messages`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Mesajlar alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function sendMyTicketMessage(
  ticketId: number,
  body: string,
  token: string | null
): Promise<TicketMessage> {
  const res = await fetch(`${API_BASE_URL}/me/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ body }),
  });

  if (!res.ok) {
    throw new Error(`Mesaj gönderilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchTicket(id: number, token: string | null): Promise<Ticket> {
  const res = await fetch(`${API_BASE_URL}/tickets/${id}`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Talep alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchDrafts(ticketId: number, token: string | null): Promise<DraftResponse[]> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/drafts`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Taslaklar alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function generateDraft(ticketId: number, token: string | null): Promise<DraftResponse> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/draft`, {
    method: "POST",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Taslak oluşturulamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export interface KbSuggestion {
  id: number;
  ticket_id: number;
  question: string;
  answer: string;
  category: string;
  intent: string;
  status: "pending" | "approved" | "rejected";
  kb_chunk_id: number | null;
  created_at: string;
  updated_at: string;
}

export async function fetchKbSuggestions(ticketId: number, token: string | null): Promise<KbSuggestion[]> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/kb-suggestions`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`SSS önerileri alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function generateKbSuggestion(ticketId: number, token: string | null): Promise<KbSuggestion> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/kb-suggestion`, {
    method: "POST",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`SSS önerisi oluşturulamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export type KbSuggestionDecision = "approved" | "rejected";

export async function updateKbSuggestionStatus(
  ticketId: number,
  suggestionId: number,
  decision: KbSuggestionDecision,
  token: string | null,
  edits?: { question?: string; answer?: string }
): Promise<KbSuggestion> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/kb-suggestions/${suggestionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ status: decision, ...edits }),
  });

  if (!res.ok) {
    throw new Error(`SSS önerisi güncellenemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface Company {
  slug: string;
  name: string;
}

// Bir şirketin talep formunun/portalın başlığında adını göstermek için —
// Clerk oturumu istemez, herkese açık (bkz. backend/app/routers/public.py).
export async function fetchCompany(slug: string): Promise<Company> {
  const res = await fetch(`${API_BASE_URL}/public/companies/${slug}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Şirket bulunamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export interface PublicTicketSubmission {
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
}

// Gerçek müşterilerin kullandığı, Clerk oturumu GEREKTİRMEYEN tek uç nokta —
// bkz. backend/app/routers/public.py. Bilinçli olarak authHeaders kullanmıyor.
// `slug`, talebin hangi şirkete gideceğini belirtir (bkz. app/support/[slug]).
export async function submitPublicTicket(payload: PublicTicketSubmission, slug: string): Promise<Ticket> {
  const res = await fetch(`${API_BASE_URL}/public/companies/${slug}/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Talep gönderilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface Me {
  clerk_user_id: string;
  is_agent: boolean;
  name: string;
  company_name: string | null;
}

export interface MyTicket {
  id: number;
  subject: string;
  body: string;
  created_at: string;
  answer: string | null;
  // Yanıta verilen hızlı 👍/👎 tepkisi — yanıt yoksa ya da henüz tepki
  // verilmediyse null.
  reaction: "up" | "down" | null;
  company_name: string;
  company_slug: string;
}

// Giriş yapan kişinin temsilci mi müşteri mi olduğunu döner — kök sayfa
// (app/page.tsx) buna göre /dashboard veya /portal'a yönlendirir.
export async function fetchMe(token: string | null): Promise<Me> {
  const res = await fetch(`${API_BASE_URL}/me`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Kullanıcı bilgisi alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchMyTickets(token: string | null): Promise<MyTicket[]> {
  const res = await fetch(`${API_BASE_URL}/me/tickets`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Talepleriniz alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchMyTicket(id: number, token: string | null): Promise<MyTicket> {
  const res = await fetch(`${API_BASE_URL}/me/tickets/${id}`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Talep alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function submitTicketReaction(
  ticketId: number,
  reaction: "up" | "down" | null,
  token: string | null
): Promise<MyTicket> {
  const res = await fetch(`${API_BASE_URL}/me/tickets/${ticketId}/reaction`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ reaction }),
  });

  if (!res.ok) {
    throw new Error(`Tepki kaydedilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface MyTicketSubmission {
  subject: string;
  body: string;
  company_slug: string;
}

// Ad/e-posta burada YOK — backend bunları Clerk oturumundan okur (bkz.
// backend/app/services/clerk_users.py), böylece biri başkasının adına talep
// açamaz.
export async function submitMyTicket(payload: MyTicketSubmission, token: string | null): Promise<MyTicket> {
  const res = await fetch(`${API_BASE_URL}/me/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Talep gönderilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface AgentInvite {
  id: number;
  token: string;
  email: string;
  name: string | null;
  invited_by: string;
  expires_at: string;
  created_at: string;
  accepted_at: string | null;
  status: "pending" | "accepted" | "expired";
}

export interface AgentInviteSubmission {
  email: string;
  name?: string;
}

export async function fetchAgentInvites(token: string | null): Promise<AgentInvite[]> {
  const res = await fetch(`${API_BASE_URL}/agent-invites`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Davetler alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function createAgentInvite(
  payload: AgentInviteSubmission,
  token: string | null
): Promise<AgentInvite> {
  const res = await fetch(`${API_BASE_URL}/agent-invites`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Davet oluşturulamadı (HTTP ${res.status})`);
  }

  return res.json();
}

// Kimlik doğrulaması istemez — davet linkine tıklayan kişi giriş yapmadan
// önce "kim davet etti" bilgisini görebilsin diye (bkz. backend/app/routers/agent_invites.py).
export async function fetchInvitePreview(token: string): Promise<AgentInvite> {
  const res = await fetch(`${API_BASE_URL}/agent-invites/${token}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Davet bulunamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function acceptAgentInvite(inviteToken: string, authToken: string | null): Promise<AgentInvite> {
  const res = await fetch(`${API_BASE_URL}/agent-invites/${inviteToken}/accept`, {
    method: "POST",
    headers: authHeaders(authToken),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Davet kabul edilemedi (HTTP ${res.status})`);
  }

  return res.json();
}

export interface TicketTotals {
  total: number;
  answered: number;
  without_draft: number;
}

export interface DraftTotals {
  total: number;
  pending: number;
  approved: number;
  edited: number;
  rejected: number;
  average_confidence: number | null;
  escalated: number;
  approval_rate: number | null;
}

export interface DailyTicketCount {
  date: string;
  count: number;
}

// DraftTotals'ın günlük hâli — zaman içindeki AI performans trendi için.
export interface DraftTrendPoint extends DraftTotals {
  date: string;
}

export interface Analytics {
  tickets: TicketTotals;
  drafts: DraftTotals;
  daily_ticket_counts: DailyTicketCount[];
  draft_trend: DraftTrendPoint[];
}

export async function fetchAnalytics(token: string | null): Promise<Analytics> {
  const res = await fetch(`${API_BASE_URL}/analytics`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Analitik veriler alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

// Hangi kategoride AI sık sık düşük güvenle/eskalasyona düşerek taslak
// ürettiği — şirketin SSS'inde muhtemelen eksik olan konuları işaret eder.
export interface KnowledgeGap {
  category: string;
  escalated_count: number;
  total_count: number;
  sample_subjects: string[];
}

export async function fetchKnowledgeGaps(token: string | null): Promise<KnowledgeGap[]> {
  const res = await fetch(`${API_BASE_URL}/analytics/knowledge-gaps`, {
    cache: "no-store",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    throw new Error(`Bilgi tabanı boşlukları alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function updateDraftStatus(
  ticketId: number,
  draftId: number,
  decision: DraftDecision,
  token: string | null,
  draftText?: string
): Promise<DraftResponse> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/drafts/${draftId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ status: decision, draft_text: draftText ?? null }),
  });

  if (!res.ok) {
    throw new Error(`Taslak güncellenemedi (HTTP ${res.status})`);
  }

  return res.json();
}

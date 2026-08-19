export interface Ticket {
  id: number;
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
  channel: string;
  category: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  is_answered: boolean;
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
  retrieved_context: RetrievedContextItem[];
  confidence_score: number | null;
  status: string;
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

export async function fetchTickets(token: string | null): Promise<Ticket[]> {
  const res = await fetch(`${API_BASE_URL}/tickets`, { cache: "no-store", headers: authHeaders(token) });

  if (!res.ok) {
    throw new Error(`Destek talepleri alınamadı (HTTP ${res.status})`);
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

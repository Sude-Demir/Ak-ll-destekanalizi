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

export interface PublicTicketSubmission {
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
}

// Gerçek müşterilerin kullandığı, Clerk oturumu GEREKTİRMEYEN tek uç nokta —
// bkz. backend/app/routers/public.py. Bilinçli olarak authHeaders kullanmıyor.
export async function submitPublicTicket(payload: PublicTicketSubmission): Promise<Ticket> {
  const res = await fetch(`${API_BASE_URL}/public/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Talep gönderilemedi (HTTP ${res.status})`);
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

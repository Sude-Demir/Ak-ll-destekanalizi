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
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchTickets(): Promise<Ticket[]> {
  const res = await fetch(`${API_BASE_URL}/tickets`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Destek talepleri alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchTicket(id: number): Promise<Ticket> {
  const res = await fetch(`${API_BASE_URL}/tickets/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Talep alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchDrafts(ticketId: number): Promise<DraftResponse[]> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/drafts`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Taslaklar alınamadı (HTTP ${res.status})`);
  }

  return res.json();
}

export async function generateDraft(ticketId: number): Promise<DraftResponse> {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/draft`, { method: "POST" });

  if (!res.ok) {
    throw new Error(`Taslak oluşturulamadı (HTTP ${res.status})`);
  }

  return res.json();
}

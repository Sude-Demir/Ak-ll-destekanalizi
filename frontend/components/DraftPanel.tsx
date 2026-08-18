"use client";

import { useState } from "react";

import StatusPill from "@/components/StatusPill";
import { generateDraft, updateDraftStatus, type DraftResponse } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  pending: "Onay bekliyor",
  approved: "Onaylandı",
  edited: "Düzenlendi",
  rejected: "Reddedildi",
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-status-open-bg text-status-open-fg",
  approved: "bg-status-done-bg text-status-done-fg",
  edited: "bg-status-wait-bg text-status-wait-fg",
  rejected: "bg-surface-2 text-muted",
};

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

function formatConfidence(score: number | null): string {
  if (score === null) return "—";
  return `%${Math.round(score * 100)}`;
}

function DraftCard({
  draft,
  ticketId,
  onUpdated,
}: {
  draft: DraftResponse;
  ticketId: number;
  onUpdated: (updated: DraftResponse) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(draft.draft_text);
  const [submitting, setSubmitting] = useState<"approved" | "edited" | "rejected" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = draft.status === "pending";

  async function handleDecision(decision: "approved" | "edited" | "rejected", text?: string) {
    setSubmitting(decision);
    setError(null);
    try {
      const updated = await updateDraftStatus(ticketId, draft.id, decision, text);
      onUpdated(updated);
      setIsEditing(false);
    } catch {
      setError("İşlem kaydedilemedi. Backend'in çalıştığından emin olun.");
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border border-l-[3px] border-l-accent bg-surface shadow-sm">
      <div className="flex items-center justify-between gap-3 bg-accent-soft px-5 py-3">
        <div className="flex items-center gap-2">
          <StatusPill
            label={STATUS_LABELS[draft.status] ?? draft.status}
            className={STATUS_STYLES[draft.status] ?? "bg-surface-2 text-muted"}
          />
          {isPending && draft.needs_escalation && (
            <StatusPill label="Dikkatli incele" className="bg-status-open-bg text-status-open-fg" />
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[12px] font-semibold tabular-nums text-muted">
            Güven: {formatConfidence(draft.confidence_score)}
          </span>
          <span className="text-[12px] tabular-nums text-muted">{formatDate(draft.created_at)}</span>
        </div>
      </div>

      <div className="px-5 py-5">
        {isEditing ? (
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            rows={6}
            className="w-full rounded-lg border border-border bg-surface-2 p-3 text-[14.5px] text-foreground focus:border-accent focus:outline-none"
          />
        ) : (
          <p className="whitespace-pre-wrap text-[14.5px] text-foreground">{draft.draft_text}</p>
        )}

        {draft.retrieved_context.length > 0 && (
          <div className="mt-4 border-t border-border pt-3.5">
            <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
              Bu taslak şu SSS içeriklerine dayanıyor
            </p>
            <ul className="mt-2.5 divide-y divide-border">
              {draft.retrieved_context.map((item) => (
                <li key={item.chunk_id} className="flex items-baseline gap-2.5 py-2 text-[12.5px]">
                  <span className="shrink-0 rounded-md border border-border bg-surface-2 px-2 py-0.5 text-[11px] font-semibold text-muted">
                    {item.category}
                  </span>
                  <span className="text-muted">{item.question}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {error && <p className="mt-3 text-[13px] text-red-600">{error}</p>}

        {isPending && (
          <div className="mt-4 flex items-center gap-2 border-t border-border pt-4">
            {isEditing ? (
              <>
                <button
                  onClick={() => handleDecision("edited", editedText)}
                  disabled={submitting !== null || !editedText.trim()}
                  className="rounded-lg bg-accent px-3.5 py-1.5 text-[13px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "edited" ? "Kaydediliyor…" : "Kaydet"}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditedText(draft.draft_text);
                  }}
                  disabled={submitting !== null}
                  className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] font-semibold text-muted hover:bg-surface-2"
                >
                  İptal
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleDecision("approved")}
                  disabled={submitting !== null}
                  className="rounded-lg bg-accent px-3.5 py-1.5 text-[13px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "approved" ? "Onaylanıyor…" : "Onayla"}
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  disabled={submitting !== null}
                  className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] font-semibold text-foreground hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Düzenle
                </button>
                <button
                  onClick={() => handleDecision("rejected")}
                  disabled={submitting !== null}
                  className="rounded-lg px-3.5 py-1.5 text-[13px] font-semibold text-muted hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "rejected" ? "Reddediliyor…" : "Reddet"}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DraftPanel({
  ticketId,
  initialDrafts,
}: {
  ticketId: number;
  initialDrafts: DraftResponse[];
}) {
  const [drafts, setDrafts] = useState(initialDrafts);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const draft = await generateDraft(ticketId);
      setDrafts((prev) => [draft, ...prev]);
    } catch {
      setError(
        "Taslak oluşturulamadı. Backend'in çalıştığından ve Gemini API anahtarının geçerli olduğundan emin olun."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleDraftUpdated(updated: DraftResponse) {
    setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
  }

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-[16px] font-bold tracking-tight text-foreground">Yanıt Taslakları</h2>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="rounded-lg bg-accent px-4 py-2 text-[13.5px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Oluşturuluyor…" : "Taslak Oluştur"}
        </button>
      </div>

      {error && <p className="mt-3 text-[13.5px] text-red-600">{error}</p>}

      <div className="mt-4 space-y-4">
        {drafts.length === 0 ? (
          <p className="text-[13.5px] text-muted">
            Bu talep için henüz bir taslak yok. Oluşturmak için yukarıdaki butona tıkla.
          </p>
        ) : (
          drafts.map((draft) => (
            <DraftCard key={draft.id} draft={draft} ticketId={ticketId} onUpdated={handleDraftUpdated} />
          ))
        )}
      </div>
    </div>
  );
}

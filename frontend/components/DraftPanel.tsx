"use client";

import { useState } from "react";

import StatusPill from "@/components/StatusPill";
import { generateDraft, type DraftResponse } from "@/lib/api";

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

function DraftCard({ draft }: { draft: DraftResponse }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border border-l-[3px] border-l-accent bg-surface shadow-sm">
      <div className="flex items-center justify-between bg-accent-soft px-5 py-3">
        <StatusPill
          label={STATUS_LABELS[draft.status] ?? draft.status}
          className={STATUS_STYLES[draft.status] ?? "bg-surface-2 text-muted"}
        />
        <span className="text-[12px] tabular-nums text-muted">{formatDate(draft.created_at)}</span>
      </div>

      <div className="px-5 py-5">
        <p className="whitespace-pre-wrap text-[14.5px] text-foreground">{draft.draft_text}</p>

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
          drafts.map((draft) => <DraftCard key={draft.id} draft={draft} />)
        )}
      </div>
    </div>
  );
}

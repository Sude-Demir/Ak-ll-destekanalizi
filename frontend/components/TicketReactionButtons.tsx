"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { submitTicketReaction } from "@/lib/api";

// Müşterinin, portaldaki yanıta verdiği hızlı 👍/👎 tepkisi — AI kalitesi
// hakkında ekip dışından gelen ilk gerçek sinyal (bkz. CLAUDE.md "özgün 10
// özellik" listesi #3). Aynı butona tekrar basmak tepkiyi temizler.
export default function TicketReactionButtons({
  ticketId,
  initialReaction,
}: {
  ticketId: number;
  initialReaction: "up" | "down" | null;
}) {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const [reaction, setReaction] = useState(initialReaction);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick(value: "up" | "down") {
    const next = reaction === value ? null : value;
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      const updated = await submitTicketReaction(ticketId, next, token);
      setReaction(updated.reaction);
    } catch {
      setError(t("portalTicketDetail.reactionError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-4 flex items-center gap-3 border-t border-border pt-3.5">
      <span className="text-[12.5px] text-muted">{t("portalTicketDetail.reactionPrompt")}</span>
      <button
        type="button"
        onClick={() => handleClick("up")}
        disabled={submitting}
        aria-pressed={reaction === "up"}
        className={`rounded-lg border px-2.5 py-1 text-[15px] transition disabled:cursor-not-allowed disabled:opacity-50 ${
          reaction === "up" ? "border-accent bg-accent-soft" : "border-border hover:bg-surface-2"
        }`}
      >
        👍
      </button>
      <button
        type="button"
        onClick={() => handleClick("down")}
        disabled={submitting}
        aria-pressed={reaction === "down"}
        className={`rounded-lg border px-2.5 py-1 text-[15px] transition disabled:cursor-not-allowed disabled:opacity-50 ${
          reaction === "down" ? "border-accent bg-accent-soft" : "border-border hover:bg-surface-2"
        }`}
      >
        👎
      </button>
      {reaction && !error && <span className="text-[12px] text-muted">{t("portalTicketDetail.reactionThanks")}</span>}
      {error && <span className="text-[12px] text-red-600">{error}</span>}
    </div>
  );
}

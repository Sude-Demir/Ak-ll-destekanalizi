"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { sendMyTicketMessage, sendTicketMessage, type TicketMessage } from "@/lib/api";
import { formatDate } from "@/lib/i18n";

// İlk AI destekli yanıttan sonraki serbest metin konuşma iş parçacığı — hem
// müşteri portalında hem temsilci panelinde aynı bileşen kullanılıyor,
// `role`'e göre hangi uç noktanın çağrılacağına karar veriliyor (bkz.
// CLAUDE.md "özgün 10 özellik" listesi #6).
export default function MessageThread({
  ticketId,
  role,
  initialMessages,
}: {
  ticketId: number;
  role: "agent" | "customer";
  initialMessages: TicketMessage[];
}) {
  const { getToken } = useAuth();
  const { locale, t } = useLocale();
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!draft.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      const send = role === "agent" ? sendTicketMessage : sendMyTicketMessage;
      const message = await send(ticketId, draft.trim(), token);
      setMessages((prev) => [...prev, message]);
      setDraft("");
    } catch {
      setError(t("messageThread.sendError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-8">
      <h2 className="text-[16px] font-bold tracking-tight text-foreground">{t("messageThread.heading")}</h2>

      {messages.length > 0 && (
        <ul className="mt-4 space-y-3">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`rounded-xl border border-border p-3.5 ${
                message.sender_type === role ? "bg-accent-soft" : "bg-surface"
              }`}
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[12.5px] font-semibold text-foreground">
                  {message.sender_name}
                  <span className="ml-1.5 text-[11px] font-normal text-faint">
                    (
                    {t(message.sender_type === "agent" ? "messageThread.roleAgent" : "messageThread.roleCustomer")}
                    )
                  </span>
                </span>
                <span className="shrink-0 text-[11.5px] tabular-nums text-faint">
                  {formatDate(message.created_at, locale)}
                </span>
              </div>
              <p className="mt-1.5 whitespace-pre-wrap text-[13.5px] text-foreground">{message.body}</p>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={t("messageThread.placeholder")}
          rows={3}
          className="w-full rounded-lg border border-border bg-surface p-3 text-[14px] text-foreground focus:border-accent focus:outline-none"
        />
        <div className="mt-2 flex items-center gap-3">
          <button
            onClick={handleSend}
            disabled={submitting || !draft.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-[13.5px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? t("messageThread.sending") : t("messageThread.send")}
          </button>
          {error && <span className="text-[12.5px] text-red-600">{error}</span>}
        </div>
      </div>
    </div>
  );
}

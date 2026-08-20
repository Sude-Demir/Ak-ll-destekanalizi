"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import CategoryBadge from "@/components/CategoryBadge";
import { useLocale } from "@/components/LocaleProvider";
import StatusPill from "@/components/StatusPill";
import { bulkApproveTickets, bulkGenerateDrafts, type Ticket } from "@/lib/api";
import { formatDate } from "@/lib/i18n";

const GRID_COLS = "grid-cols-[28px_1.9fr_0.9fr_0.7fr_0.9fr_0.9fr]";

export default function TicketsTable({
  tickets,
  emptyMessage,
}: {
  tickets: Ticket[];
  emptyMessage?: string;
}) {
  const { locale, t } = useLocale();
  const { getToken } = useAuth();
  const router = useRouter();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [approving, setApproving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (tickets.length === 0) {
    return <p className="mt-6 text-muted">{emptyMessage ?? t("ticketsTable.empty")}</p>;
  }

  function toggle(ticketId: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(ticketId)) next.delete(ticketId);
      else next.add(ticketId);
      return next;
    });
  }

  // Seçili talepler iki gruba ayrılır: bir taslağı onay bekleyenler ("Onayla"
  // ile ilerler) ve hiç taslağı olmayanlar ("Taslak Oluştur" ile ilerler).
  // Karışık bir seçimde iki buton da görünür, her biri sadece kendi grubunu
  // işler.
  const selectedTickets = tickets.filter((ticket) => selected.has(ticket.id));
  const approveIds = selectedTickets.filter((ticket) => ticket.pending_draft_id !== null).map((ticket) => ticket.id);
  const generateIds = selectedTickets.filter((ticket) => ticket.pending_draft_id === null).map((ticket) => ticket.id);

  async function handleBulkApprove() {
    setApproving(true);
    setError(null);
    try {
      const token = await getToken();
      await bulkApproveTickets(approveIds, token);
      setSelected(new Set());
      router.refresh();
    } catch {
      setError(t("ticketsTable.bulkApproveError"));
    } finally {
      setApproving(false);
    }
  }

  async function handleBulkGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const token = await getToken();
      const result = await bulkGenerateDrafts(generateIds, token);
      setSelected(new Set());
      if (result.failed.length > 0) {
        setError(t("ticketsTable.bulkGeneratePartialError", { count: result.failed.length }));
      }
      router.refresh();
    } catch {
      setError(t("ticketsTable.bulkGenerateError"));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
      {selected.size > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-accent-soft px-5 py-2.5">
          <span className="text-[13px] font-semibold text-accent">
            {t("ticketsTable.selectedCount", { count: selected.size })}
          </span>
          <div className="flex items-center gap-3">
            {error && <span className="text-[12.5px] text-red-600">{error}</span>}
            {approveIds.length > 0 && (
              <button
                type="button"
                onClick={handleBulkApprove}
                disabled={approving || generating}
                className="rounded-lg bg-accent px-3.5 py-1.5 text-[13px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
              >
                {approving
                  ? t("ticketsTable.bulkApproving")
                  : t("ticketsTable.bulkApproveCount", { count: approveIds.length })}
              </button>
            )}
            {generateIds.length > 0 && (
              <button
                type="button"
                onClick={handleBulkGenerate}
                disabled={approving || generating}
                className="rounded-lg border border-accent px-3.5 py-1.5 text-[13px] font-semibold text-accent hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
              >
                {generating
                  ? t("ticketsTable.bulkGenerating")
                  : t("ticketsTable.bulkGenerateCount", { count: generateIds.length })}
              </button>
            )}
          </div>
        </div>
      )}

      <div role="table" aria-label={t("ticketsTable.ariaLabel")} className="min-w-full text-sm">
        <div role="row" className={`grid ${GRID_COLS} items-center gap-4 bg-surface-2 px-5 py-3 text-[11.5px] font-bold tracking-wide text-faint uppercase`}>
          <span aria-hidden="true" />
          <span role="columnheader">{t("ticketsTable.subject")}</span>
          <span role="columnheader">{t("ticketsTable.category")}</span>
          <span role="columnheader">{t("ticketsTable.channel")}</span>
          <span role="columnheader">{t("ticketsTable.answer")}</span>
          <span role="columnheader">{t("ticketsTable.createdAt")}</span>
        </div>

        <div role="rowgroup" className="divide-y divide-border">
          {tickets.map((ticket) => (
            <div key={ticket.id} role="row" className={`grid ${GRID_COLS} items-center gap-4 px-5 py-3.5 hover:bg-surface-2`}>
              <div role="cell">
                <input
                  type="checkbox"
                  checked={selected.has(ticket.id)}
                  onChange={() => toggle(ticket.id)}
                  disabled={ticket.is_answered}
                  aria-label={t("ticketsTable.selectRow", { subject: ticket.subject })}
                  className="h-4 w-4 rounded border-border-strong accent-accent disabled:cursor-not-allowed disabled:opacity-30"
                />
              </div>
              <Link href={`/dashboard/tickets/${ticket.id}`} role="cell" className="min-w-0">
                <div className="truncate text-[13.8px] font-semibold text-foreground">{ticket.subject}</div>
                <div className="truncate text-[12.5px] text-muted">
                  {ticket.customer_name} · {ticket.customer_email}
                </div>
              </Link>
              <div role="cell">
                <CategoryBadge category={ticket.category} locale={locale} />
              </div>
              <div role="cell" className="text-[12.5px] text-muted">
                {ticket.channel}
              </div>
              <div role="cell">
                <StatusPill
                  label={ticket.is_answered ? t("ticketsTable.answered") : t("ticketsTable.unanswered")}
                  className={
                    ticket.is_answered
                      ? "bg-status-done-bg text-status-done-fg"
                      : "bg-status-open-bg text-status-open-fg"
                  }
                />
              </div>
              <div role="cell" className="whitespace-nowrap text-[12.5px] tabular-nums text-faint">
                {formatDate(ticket.created_at, locale)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

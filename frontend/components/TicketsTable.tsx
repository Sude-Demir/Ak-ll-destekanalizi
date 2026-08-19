import Link from "next/link";

import CategoryBadge from "@/components/CategoryBadge";
import StatusPill from "@/components/StatusPill";
import { formatDate, t, type Locale } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import type { Ticket } from "@/lib/api";

export const TICKET_STATUS_LABELS: Record<Locale, Record<string, string>> = {
  tr: { open: "Açık", pending: "Beklemede", closed: "Kapalı" },
  en: { open: "Open", pending: "Pending", closed: "Closed" },
};

export const TICKET_STATUS_STYLES: Record<string, string> = {
  open: "bg-status-open-bg text-status-open-fg",
  pending: "bg-status-wait-bg text-status-wait-fg",
  closed: "bg-status-done-bg text-status-done-fg",
};

export default async function TicketsTable({
  tickets,
  emptyMessage,
}: {
  tickets: Ticket[];
  emptyMessage?: string;
}) {
  const locale = await getLocale();

  if (tickets.length === 0) {
    return <p className="mt-6 text-muted">{emptyMessage ?? t(locale, "ticketsTable.empty")}</p>;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
      <div
        role="table"
        aria-label={t(locale, "ticketsTable.ariaLabel")}
        className="min-w-full text-sm"
      >
        <div
          role="row"
          className="grid grid-cols-[1.9fr_0.9fr_0.7fr_0.9fr_0.9fr] gap-4 bg-surface-2 px-5 py-3 text-[11.5px] font-bold tracking-wide text-faint uppercase"
        >
          <span role="columnheader">{t(locale, "ticketsTable.subject")}</span>
          <span role="columnheader">{t(locale, "ticketsTable.category")}</span>
          <span role="columnheader">{t(locale, "ticketsTable.channel")}</span>
          <span role="columnheader">{t(locale, "ticketsTable.answer")}</span>
          <span role="columnheader">{t(locale, "ticketsTable.createdAt")}</span>
        </div>

        <div role="rowgroup" className="divide-y divide-border">
          {tickets.map((ticket) => (
            <Link
              key={ticket.id}
              href={`/dashboard/tickets/${ticket.id}`}
              role="row"
              className="grid grid-cols-[1.9fr_0.9fr_0.7fr_0.9fr_0.9fr] items-center gap-4 px-5 py-3.5 transition-colors hover:bg-surface-2"
            >
              <div role="cell" className="min-w-0">
                <div className="truncate text-[13.8px] font-semibold text-foreground">
                  {ticket.subject}
                </div>
                <div className="truncate text-[12.5px] text-muted">
                  {ticket.customer_name} · {ticket.customer_email}
                </div>
              </div>
              <div role="cell">
                <CategoryBadge category={ticket.category} locale={locale} />
              </div>
              <div role="cell" className="text-[12.5px] text-muted">
                {ticket.channel}
              </div>
              <div role="cell">
                <StatusPill
                  label={ticket.is_answered ? t(locale, "ticketsTable.answered") : t(locale, "ticketsTable.unanswered")}
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
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";

import StatusPill from "@/components/StatusPill";
import type { MyTicket } from "@/lib/api";
import { formatDate, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function MyTicketsList({ tickets }: { tickets: MyTicket[] }) {
  const locale = await getLocale();

  if (tickets.length === 0) {
    return <p className="mt-6 text-muted">{t(locale, "myTickets.empty")}</p>;
  }

  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
      <div role="table" aria-label={t(locale, "myTickets.ariaLabel")} className="min-w-full text-sm">
        <div role="rowgroup" className="divide-y divide-border">
          {tickets.map((ticket) => (
            <Link
              key={ticket.id}
              href={`/portal/tickets/${ticket.id}`}
              role="row"
              className="flex items-center justify-between gap-4 px-5 py-3.5 transition-colors hover:bg-surface-2"
            >
              <div className="min-w-0">
                <div className="truncate text-[13.8px] font-semibold text-foreground">{ticket.subject}</div>
                <div className="truncate text-[12.5px] text-muted">{formatDate(ticket.created_at, locale)}</div>
              </div>
              <StatusPill
                label={ticket.answer ? t(locale, "myTickets.answered") : t(locale, "myTickets.pending")}
                className={
                  ticket.answer
                    ? "bg-status-done-bg text-status-done-fg"
                    : "bg-status-wait-bg text-status-wait-fg"
                }
              />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

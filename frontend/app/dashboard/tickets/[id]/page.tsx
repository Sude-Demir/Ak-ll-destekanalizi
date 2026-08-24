import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import DraftPanel from "@/components/DraftPanel";
import KbSuggestionPanel from "@/components/KbSuggestionPanel";
import MessageThread from "@/components/MessageThread";
import StatusPill from "@/components/StatusPill";
import TicketAssignmentButton from "@/components/TicketAssignmentButton";
import { fetchDrafts, fetchKbSuggestions, fetchTicket, fetchTicketMessages, fetchTickets, type Ticket } from "@/lib/api";
import { formatDate, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import { TICKET_STATUS_LABELS, TICKET_STATUS_STYLES } from "@/lib/ticketStatus";

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const locale = await getLocale();
  const { id } = await params;
  const ticketId = Number(id);

  if (Number.isNaN(ticketId)) {
    notFound();
  }

  const { getToken } = await auth();
  const token = await getToken();

  let ticket;
  let drafts;
  let kbSuggestions;
  let messages;
  try {
    [ticket, drafts, kbSuggestions, messages] = await Promise.all([
      fetchTicket(ticketId, token),
      fetchDrafts(ticketId, token),
      fetchKbSuggestions(ticketId, token),
      fetchTicketMessages(ticketId, token),
    ]);
  } catch {
    notFound();
  }

  // Aynı müşterinin diğer talepleri — bağlamsal bir bilgi, yüklenemezse
  // sayfanın geri kalanını bozmasın diye ayrı bir try/catch'te.
  let customerHistory: Ticket[] = [];
  try {
    const history = await fetchTickets(token, { customerEmail: ticket.customer_email });
    customerHistory = history.items.filter((other) => other.id !== ticket.id);
  } catch {
    // Sessizce boş bırak.
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link
        href="/dashboard"
        className="text-[13px] font-semibold text-muted hover:text-foreground"
      >
        {t(locale, "ticketDetail.back")}
      </Link>

      <div className="mt-4 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-[17px] font-bold tracking-tight text-foreground text-balance">
              {ticket.subject}
            </h1>
            <p className="mt-1 text-[12.5px] text-muted">
              {ticket.customer_name} · {ticket.customer_email}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {ticket.is_lead && (
              <StatusPill label={t(locale, "ticketsTable.leadBadge")} className="bg-accent-soft text-accent" />
            )}
            {ticket.is_urgent && (
              <StatusPill label={t(locale, "ticketsTable.urgentBadge")} className="bg-red-50 text-red-700" />
            )}
            <StatusPill
              label={TICKET_STATUS_LABELS[locale][ticket.status] ?? ticket.status}
              className={TICKET_STATUS_STYLES[ticket.status] ?? "bg-surface-2 text-muted"}
            />
          </div>
        </div>

        <p className="mt-4 whitespace-pre-wrap rounded-lg border border-border bg-surface-2 p-4 text-[14px] text-foreground">
          {ticket.body}
        </p>

        <dl className="mt-4 grid grid-cols-3 gap-4 border-t border-border pt-4">
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">
              {t(locale, "ticketDetail.channel")}
            </dt>
            <dd className="mt-1 text-[13.5px] font-semibold text-foreground">{ticket.channel}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">
              {t(locale, "ticketDetail.category")}
            </dt>
            <dd className="mt-1 text-[13.5px] font-semibold text-foreground">
              {ticket.category ?? t(locale, "ticketDetail.unclassified")}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">
              {t(locale, "ticketDetail.createdAt")}
            </dt>
            <dd className="mt-1 text-[13.5px] font-semibold tabular-nums text-foreground">
              {formatDate(ticket.created_at, locale)}
            </dd>
          </div>
        </dl>

        <div className="mt-4 border-t border-border pt-4">
          <TicketAssignmentButton ticketId={ticket.id} initialAssignedAgentName={ticket.assigned_agent_name} />
        </div>
      </div>

      <DraftPanel ticketId={ticket.id} initialDrafts={drafts} />

      <KbSuggestionPanel ticketId={ticket.id} isAnswered={ticket.is_answered} initialSuggestions={kbSuggestions} />

      <MessageThread ticketId={ticket.id} role="agent" initialMessages={messages} />

      {customerHistory.length > 0 && (
        <div className="mt-8 rounded-xl border border-border bg-surface p-5 shadow-sm">
          <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
            {t(locale, "ticketDetail.customerHistoryHeading")}
          </p>
          <ul className="mt-3 divide-y divide-border">
            {customerHistory.map((other) => (
              <li key={other.id}>
                <Link
                  href={`/dashboard/tickets/${other.id}`}
                  className="flex items-center justify-between gap-3 py-2.5 hover:text-accent"
                >
                  <span className="min-w-0 truncate text-[13px] text-foreground">{other.subject}</span>
                  <span className="flex shrink-0 items-center gap-2.5">
                    <StatusPill
                      label={other.is_answered ? t(locale, "ticketsTable.answered") : t(locale, "ticketsTable.unanswered")}
                      className={
                        other.is_answered
                          ? "bg-status-done-bg text-status-done-fg"
                          : "bg-status-open-bg text-status-open-fg"
                      }
                    />
                    <span className="text-[12px] tabular-nums text-faint">{formatDate(other.created_at, locale)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}

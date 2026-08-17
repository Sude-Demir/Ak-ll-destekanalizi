import Link from "next/link";
import { notFound } from "next/navigation";

import DraftPanel from "@/components/DraftPanel";
import StatusPill from "@/components/StatusPill";
import { TICKET_STATUS_LABELS, TICKET_STATUS_STYLES } from "@/components/TicketsTable";
import { fetchDrafts, fetchTicket } from "@/lib/api";

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const ticketId = Number(id);

  if (Number.isNaN(ticketId)) {
    notFound();
  }

  let ticket;
  let drafts;
  try {
    [ticket, drafts] = await Promise.all([fetchTicket(ticketId), fetchDrafts(ticketId)]);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link
        href="/dashboard"
        className="text-[13px] font-semibold text-muted hover:text-foreground"
      >
        ← Tüm taleplere dön
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
          <StatusPill
            label={TICKET_STATUS_LABELS[ticket.status] ?? ticket.status}
            className={TICKET_STATUS_STYLES[ticket.status] ?? "bg-surface-2 text-muted"}
          />
        </div>

        <p className="mt-4 whitespace-pre-wrap rounded-lg border border-border bg-surface-2 p-4 text-[14px] text-foreground">
          {ticket.body}
        </p>

        <dl className="mt-4 grid grid-cols-3 gap-4 border-t border-border pt-4">
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">Kanal</dt>
            <dd className="mt-1 text-[13.5px] font-semibold text-foreground">{ticket.channel}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">Kategori</dt>
            <dd className="mt-1 text-[13.5px] font-semibold text-foreground">
              {ticket.category ?? "Henüz sınıflandırılmadı"}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold tracking-wide text-faint uppercase">
              Oluşturulma
            </dt>
            <dd className="mt-1 text-[13.5px] font-semibold tabular-nums text-foreground">
              {formatDate(ticket.created_at)}
            </dd>
          </div>
        </dl>
      </div>

      <DraftPanel ticketId={ticket.id} initialDrafts={drafts} />
    </main>
  );
}

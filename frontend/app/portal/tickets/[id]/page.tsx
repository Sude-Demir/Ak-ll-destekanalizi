import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchMyTicket } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function MyTicketDetailPage({
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
  try {
    ticket = await fetchMyTicket(ticketId, token);
  } catch {
    // Talep bulunamadı ya da başkasına ait — backend her iki durumda da 404
    // döner (bkz. backend/app/routers/me.py get_my_ticket).
    notFound();
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <Link href="/portal" className="text-[13px] font-semibold text-accent hover:underline">
        {t(locale, "portalTicketDetail.back")}
      </Link>

      <h1 className="mt-3 text-[20px] font-bold tracking-tight text-foreground">{ticket.subject}</h1>
      <p className="mt-2 whitespace-pre-wrap text-[14px] text-muted">{ticket.body}</p>

      <div className="mt-6 rounded-xl border border-border bg-surface p-6 shadow-sm">
        {ticket.answer ? (
          <>
            <span className="text-[11.5px] font-bold uppercase tracking-wide text-faint">
              {t(locale, "portalTicketDetail.answerHeading")}
            </span>
            <p className="mt-2 whitespace-pre-wrap text-[14px] text-foreground">{ticket.answer}</p>
          </>
        ) : (
          <p className="text-[14px] text-muted">{t(locale, "portalTicketDetail.pending")}</p>
        )}
      </div>
    </main>
  );
}

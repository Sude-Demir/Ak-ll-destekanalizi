import { auth } from "@clerk/nextjs/server";
import Link from "next/link";

import LandingPage from "@/components/LandingPage";
import StatusPill from "@/components/StatusPill";
import { fetchAnalytics, fetchMe, fetchMyTickets } from "@/lib/api";
import { DRAFT_STATUS_PILL_CLASSES } from "@/lib/draftStatus";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function Home() {
  const locale = await getLocale();
  const { userId, getToken } = await auth();

  // Oturum var diye otomatik olarak panele/portala atlamıyoruz — tarayıcıda
  // eski bir oturum kalmış olsa bile önce burada bilinçli bir tıklama
  // isteniyor (kullanıcı isteği: "hangi hesapta kaldığına direkt girmesin").
  if (!userId) {
    return <LandingPage />;
  }

  const token = await getToken();
  const me = await fetchMe(token);
  const firstName = me.name.split(" ")[0];

  // Bu ekran salt bir geçiş formalitesi olmasın diye (kullanıcı geri bildirimi:
  // "çok boş duruyor"), panele/portala gitmeden önce tek bir gerçek veri
  // özeti gösteriyoruz — temsilciye bekleyen taslak sayısı, müşteriye en son
  // talebinin durumu. Mevcut /analytics ve /me/tickets uç noktaları zaten bu
  // veriyi döndürüyor, yeni bir uç nokta gerekmedi.
  const analytics = me.is_agent ? await fetchAnalytics(token) : null;
  const myTickets = me.is_agent ? null : await fetchMyTickets(token);
  const latestTicket = myTickets?.[0] ?? null;

  return (
    <main className="mx-auto flex max-w-xl flex-1 flex-col items-center justify-center gap-6 px-6 py-16 text-center">
      <div className="flex flex-col items-center gap-1">
        <h1 className="text-[26px] font-bold tracking-tight text-foreground">
          {t(locale, "welcome.greeting", { name: firstName })}
        </h1>
        {me.company_name && <p className="text-[12.5px] text-faint">{me.company_name}</p>}
        <p className="mt-1 text-[14px] text-muted">
          {t(locale, me.is_agent ? "welcome.subtitleAgent" : "welcome.subtitleCustomer")}
        </p>
      </div>

      {analytics && (
        <div className="grid w-full grid-cols-2 gap-3">
          <div className="flex flex-col items-center gap-1 rounded-xl bg-accent-soft px-4 py-3.5">
            <span className="text-[24px] font-bold tabular-nums text-accent">{analytics.drafts.pending}</span>
            <span className="text-[11.5px] font-medium leading-tight text-muted">
              {t(locale, "welcome.statPendingDrafts")}
            </span>
          </div>
          <div className="flex flex-col items-center gap-1 rounded-xl bg-surface-2 px-4 py-3.5">
            <span className="text-[24px] font-bold tabular-nums text-foreground">
              {analytics.tickets.answered}/{analytics.tickets.total}
            </span>
            <span className="text-[11.5px] font-medium leading-tight text-muted">
              {t(locale, "welcome.statAnsweredTickets")}
            </span>
          </div>
        </div>
      )}

      {latestTicket && (
        <Link
          href={`/portal/tickets/${latestTicket.id}`}
          className="flex w-full items-center justify-between gap-3 rounded-xl border border-border bg-surface-2 px-4 py-3 text-left hover:bg-border/40"
        >
          <span className="flex min-w-0 flex-col gap-0.5">
            <span className="text-[10.5px] font-bold uppercase tracking-wide text-faint">
              {t(locale, "welcome.latestTicketLabel")}
            </span>
            <span className="truncate text-[13.5px] font-medium text-foreground">{latestTicket.subject}</span>
          </span>
          <StatusPill
            label={t(locale, latestTicket.answer ? "welcome.ticketAnswered" : "welcome.ticketPending")}
            className={
              latestTicket.answer ? DRAFT_STATUS_PILL_CLASSES.approved : DRAFT_STATUS_PILL_CLASSES.pending
            }
          />
        </Link>
      )}

      <Link
        href={me.is_agent ? "/dashboard" : "/portal"}
        className="rounded-lg bg-accent px-5 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong"
      >
        {t(locale, me.is_agent ? "welcome.goToDashboard" : "welcome.goToPortal")}
      </Link>
    </main>
  );
}

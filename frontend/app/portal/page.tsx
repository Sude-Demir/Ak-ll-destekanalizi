import { auth } from "@clerk/nextjs/server";

import MyTicketsList from "@/components/MyTicketsList";
import NewTicketForm from "@/components/NewTicketForm";
import { fetchMyTickets } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function PortalPage() {
  const locale = await getLocale();
  const { getToken } = await auth();
  const token = await getToken();

  let tickets;
  let errorMessage: string | null = null;

  try {
    tickets = await fetchMyTickets(token);
  } catch {
    errorMessage = t(locale, "portal.loadError");
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-[22px] font-bold tracking-tight text-foreground">{t(locale, "portal.title")}</h1>
      <p className="mt-1 text-[13.5px] text-muted">{t(locale, "portal.subtitle")}</p>

      <div className="mt-6">
        <NewTicketForm />
      </div>

      {errorMessage ? (
        <p className="mt-6 text-red-600">{errorMessage}</p>
      ) : (
        <MyTicketsList tickets={tickets ?? []} />
      )}
    </main>
  );
}

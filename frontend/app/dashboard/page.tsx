import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { redirect } from "next/navigation";

import CategoryDistribution from "@/components/CategoryDistribution";
import CategoryFilterBar from "@/components/CategoryFilterBar";
import TicketStats from "@/components/TicketStats";
import TicketsTable from "@/components/TicketsTable";
import { fetchTickets } from "@/lib/api";
import { categoryLabel, isCategory } from "@/lib/categories";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const locale = await getLocale();
  const { category } = await searchParams;
  // Bilinmeyen/bozuk bir query param'ı (?category=xyz) sessizce "Tümü"ye
  // düşer; filtre çubuğu zaten sadece geçerli 11 kategoriyi link olarak sunar.
  const activeCategory = category && isCategory(category) ? category : null;

  const { getToken } = await auth();
  const token = await getToken();

  let tickets;
  let errorMessage: string | null = null;

  try {
    tickets = await fetchTickets(token);
  } catch (error) {
    // Backend, temsilci olmayan bir kullanıcı için 403 döner (bkz.
    // backend/app/auth.py require_agent) — bu bir hata değil, kişi müşteri
    // portalına ait demektir.
    if (error instanceof Error && error.message.includes("403")) {
      redirect("/portal");
    }
    errorMessage = t(locale, "dashboard.loadError");
  }

  const allTickets = tickets ?? [];
  const filteredTickets = activeCategory
    ? allTickets.filter((ticket) => ticket.category === activeCategory)
    : allTickets;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">{t(locale, "dashboard.title")}</h1>
          <p className="mt-1 text-[13.5px] text-muted">{t(locale, "dashboard.subtitle")}</p>
        </div>
        <Link
          href="/dashboard/team"
          className="shrink-0 rounded-lg border border-border px-3.5 py-2 text-[13px] font-semibold text-foreground hover:border-border-strong"
        >
          {t(locale, "dashboard.team")}
        </Link>
      </div>

      {errorMessage ? (
        <p className="mt-6 text-red-600">{errorMessage}</p>
      ) : (
        <>
          <TicketStats tickets={allTickets} />
          <CategoryDistribution tickets={allTickets} />
          <CategoryFilterBar tickets={allTickets} activeCategory={activeCategory} />
          <div className="mt-6">
            <TicketsTable
              tickets={filteredTickets}
              emptyMessage={
                activeCategory
                  ? t(locale, "dashboard.emptyForCategory", { category: categoryLabel(activeCategory, locale) })
                  : undefined
              }
            />
          </div>
        </>
      )}
    </main>
  );
}

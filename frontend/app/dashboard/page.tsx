import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

import CategoryDistribution from "@/components/CategoryDistribution";
import CategoryFilterBar from "@/components/CategoryFilterBar";
import Pagination from "@/components/Pagination";
import SearchBox from "@/components/SearchBox";
import TicketFilterBar from "@/components/TicketFilterBar";
import TicketStats from "@/components/TicketStats";
import TicketsTable from "@/components/TicketsTable";
import { fetchTickets, type TicketList } from "@/lib/api";
import { categoryLabel, isCategory } from "@/lib/categories";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const CHANNELS = ["twitter", "email", "form", "portal"];

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{
    category?: string;
    q?: string;
    answered?: string;
    channel?: string;
    sort?: string;
    lead?: string;
    page?: string;
  }>;
}) {
  const locale = await getLocale();
  const { category, q, answered, channel, sort, lead, page: pageParam } = await searchParams;
  // Bilinmeyen/bozuk bir query param'ı (?category=xyz) sessizce "Tümü"ye
  // düşer; filtre çubukları zaten sadece geçerli değerleri link olarak sunar.
  const activeCategory = category && isCategory(category) ? category : null;
  const activeQuery = q?.trim() ? q.trim() : null;
  const activeAnswered = answered === "true" || answered === "false" ? answered : null;
  const activeChannel = channel && CHANNELS.includes(channel) ? channel : null;
  const activeSort = sort === "oldest" ? sort : null;
  const activeLead = lead === "true" ? lead : null;
  const page = Number(pageParam);
  const currentPage = Number.isInteger(page) && page > 0 ? page : 1;

  const { getToken } = await auth();
  const token = await getToken();

  let result: TicketList | null = null;
  let errorMessage: string | null = null;

  try {
    result = await fetchTickets(token, {
      category: activeCategory ?? undefined,
      q: activeQuery ?? undefined,
      isAnswered: activeAnswered === null ? undefined : activeAnswered === "true",
      channel: activeChannel ?? undefined,
      isLead: activeLead === "true" ? true : undefined,
      sort: activeSort === "oldest" ? "oldest" : undefined,
      page: currentPage,
    });
  } catch (error) {
    // Backend, temsilci olmayan bir kullanıcı için 403 döner (bkz.
    // backend/app/auth.py require_agent) — bu bir hata değil, kişi müşteri
    // portalına ait demektir.
    if (error instanceof Error && error.message.includes("403")) {
      redirect("/portal");
    }
    errorMessage = t(locale, "dashboard.loadError");
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">{t(locale, "dashboard.title")}</h1>
          <p className="mt-1 text-[13.5px] text-muted">{t(locale, "dashboard.subtitle")}</p>
        </div>
        <SearchBox />
      </div>

      {errorMessage ? (
        <p className="mt-6 text-red-600">{errorMessage}</p>
      ) : result ? (
        <>
          <TicketStats summary={result} />
          <CategoryDistribution categoryCounts={result.category_counts} overallTotal={result.overall_total} />
          <CategoryFilterBar
            categoryCounts={result.category_counts}
            overallTotal={result.overall_total}
            activeCategory={activeCategory}
            activeQuery={activeQuery}
            activeAnswered={activeAnswered}
            activeChannel={activeChannel}
            activeSort={activeSort}
            activeLead={activeLead}
          />
          <TicketFilterBar
            activeCategory={activeCategory}
            activeQuery={activeQuery}
            activeAnswered={activeAnswered}
            activeChannel={activeChannel}
            activeSort={activeSort}
            activeLead={activeLead}
          />
          <div className="mt-6">
            <TicketsTable
              tickets={result.items}
              emptyMessage={
                activeCategory
                  ? t(locale, "dashboard.emptyForCategory", { category: categoryLabel(activeCategory, locale) })
                  : undefined
              }
            />
          </div>
          <Pagination
            page={result.page}
            pageSize={result.page_size}
            total={result.total}
            category={activeCategory}
            query={activeQuery}
            answered={activeAnswered}
            channel={activeChannel}
            sort={activeSort}
            lead={activeLead}
          />
        </>
      ) : null}
    </main>
  );
}

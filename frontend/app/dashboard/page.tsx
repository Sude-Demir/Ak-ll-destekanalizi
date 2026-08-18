import { auth } from "@clerk/nextjs/server";

import CategoryDistribution from "@/components/CategoryDistribution";
import CategoryFilterBar from "@/components/CategoryFilterBar";
import TicketStats from "@/components/TicketStats";
import TicketsTable from "@/components/TicketsTable";
import { fetchTickets } from "@/lib/api";
import { categoryLabel, isCategory } from "@/lib/categories";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
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
  } catch {
    errorMessage =
      "Destek talepleri yüklenemedi. Backend'in (http://localhost:8000) çalıştığından emin olun.";
  }

  const allTickets = tickets ?? [];
  const filteredTickets = activeCategory
    ? allTickets.filter((t) => t.category === activeCategory)
    : allTickets;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-[22px] font-bold tracking-tight text-foreground">Destek Talepleri</h1>
      <p className="mt-1 text-[13.5px] text-muted">
        Bir talebe tıklayarak detayını görüntüleyebilir ve AI destekli yanıt taslağı oluşturabilirsin.
      </p>

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
                  ? `Bu kategoride (${categoryLabel(activeCategory)}) talep yok.`
                  : undefined
              }
            />
          </div>
        </>
      )}
    </main>
  );
}

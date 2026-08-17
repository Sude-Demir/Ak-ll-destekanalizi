import TicketStats from "@/components/TicketStats";
import TicketsTable from "@/components/TicketsTable";
import { fetchTickets } from "@/lib/api";

export default async function DashboardPage() {
  let tickets;
  let errorMessage: string | null = null;

  try {
    tickets = await fetchTickets();
  } catch {
    errorMessage =
      "Destek talepleri yüklenemedi. Backend'in (http://localhost:8000) çalıştığından emin olun.";
  }

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
          <TicketStats tickets={tickets ?? []} />
          <div className="mt-6">
            <TicketsTable tickets={tickets ?? []} />
          </div>
        </>
      )}
    </main>
  );
}

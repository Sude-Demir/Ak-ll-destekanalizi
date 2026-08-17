import type { Ticket } from "@/lib/api";

function Stat({
  value,
  label,
  accent = false,
}: {
  value: number;
  label: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3.5 shadow-sm">
      <div className={`text-[22px] font-bold tracking-tight ${accent ? "text-accent" : "text-foreground"}`}>
        {value}
      </div>
      <div className="mt-0.5 text-[12.5px] text-muted">{label}</div>
    </div>
  );
}

export default function TicketStats({ tickets }: { tickets: Ticket[] }) {
  const open = tickets.filter((t) => t.status === "open").length;
  const closed = tickets.filter((t) => t.status === "closed").length;
  const classified = tickets.filter((t) => t.category !== null).length;

  return (
    <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Stat value={tickets.length} label="toplam talep" />
      <Stat value={open} label="açık" />
      <Stat value={classified} label="sınıflandırıldı" accent />
      <Stat value={closed} label="çözüldü" />
    </div>
  );
}

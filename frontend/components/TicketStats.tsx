import type { TicketList } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

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

export default async function TicketStats({ summary }: { summary: TicketList }) {
  const locale = await getLocale();

  return (
    <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Stat value={summary.overall_total} label={t(locale, "ticketStats.total")} />
      <Stat value={summary.open_count} label={t(locale, "ticketStats.open")} />
      <Stat value={summary.classified_count} label={t(locale, "ticketStats.classified")} accent />
      <Stat value={summary.resolved_count} label={t(locale, "ticketStats.resolved")} />
    </div>
  );
}

import type { Analytics } from "@/lib/api";
import { formatDay } from "@/lib/dateFormat";
import { formatPercent, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

function HeroStat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="font-mono text-[26px] font-semibold tracking-tight tabular-nums text-white sm:text-[30px]">
        {value}
      </div>
      <div className="mt-1 text-[12px] text-white/65">{label}</div>
    </div>
  );
}

// Bilinçli olarak sabit koyu bordo — tema (light/dark) değişse de aynı kalır.
// Sayfanın geri kalanı token'lardan renk alıyor; bu banner kendi kimliğine
// sahip, kendi içinde tutarlı bir "marka bandı" (bkz. plan "Analitik hero").
export default async function AnalyticsHero({ analytics }: { analytics: Analytics }) {
  const locale = await getLocale();
  const { tickets, drafts, daily_ticket_counts } = analytics;

  const answeredRate = tickets.total > 0 ? tickets.answered / tickets.total : 0;
  const approvalValue = drafts.approval_rate === null ? "—" : formatPercent(drafts.approval_rate, locale);
  const confidenceValue = drafts.average_confidence === null ? "—" : formatPercent(drafts.average_confidence, locale);

  const thesis =
    drafts.approval_rate === null
      ? t(locale, "analytics.thesisEmpty")
      : t(locale, "analytics.thesis", {
          total: tickets.total,
          answered: tickets.answered,
          rate: formatPercent(drafts.approval_rate, locale),
        });

  const period =
    daily_ticket_counts.length > 0
      ? `${formatDay(daily_ticket_counts[0].date, locale)} – ${formatDay(
          daily_ticket_counts[daily_ticket_counts.length - 1].date,
          locale
        )}`
      : null;

  return (
    <div
      className="relative overflow-hidden px-6 py-9 sm:px-10 sm:py-10"
      style={{
        backgroundImage:
          "radial-gradient(circle at 15% 20%, rgba(255,255,255,0.05), transparent 45%), linear-gradient(135deg, #4a2038, #2d1424 65%)",
      }}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.09) 1px, transparent 1px)",
          backgroundSize: "16px 16px",
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-6xl">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="font-mono text-[11px] tracking-wide text-white/60 uppercase">
            {t(locale, "analytics.title")}
          </span>
          {period && <span className="font-mono text-[11.5px] text-white/60">{period}</span>}
        </div>

        <p className="mt-2 max-w-[58ch] text-balance text-[19px] font-semibold leading-snug text-white sm:text-[22px]">
          {thesis}
        </p>

        <div className="mt-7 grid grid-cols-2 gap-5 sm:grid-cols-4">
          <HeroStat value={String(tickets.total)} label={t(locale, "analytics.totalTickets")} />
          <HeroStat
            value={`${tickets.answered} (${formatPercent(answeredRate, locale)})`}
            label={t(locale, "analytics.answeredTickets")}
          />
          <HeroStat value={approvalValue} label={t(locale, "analytics.approvalRate")} />
          <HeroStat value={confidenceValue} label={t(locale, "analytics.averageConfidence")} />
        </div>
      </div>
    </div>
  );
}

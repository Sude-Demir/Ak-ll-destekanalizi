import type { Analytics } from "@/lib/api";
import { formatDay } from "@/lib/dateFormat";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const WIDTH = 600;
const BASELINE = 120;
const TOP_PAD = 10;
const CHART_H = BASELINE - TOP_PAD;
const LEFT_PAD = 10;
const RIGHT_PAD = 10;

function buildPoints(counts: { count: number }[]) {
  const max = Math.max(...counts.map((c) => c.count));
  const stepX = counts.length > 1 ? (WIDTH - LEFT_PAD - RIGHT_PAD) / (counts.length - 1) : 0;
  return counts.map((c, i) => ({
    x: LEFT_PAD + i * stepX,
    y: BASELINE - (c.count / max) * CHART_H,
  }));
}

export default async function TicketVolumeChart({ analytics }: { analytics: Analytics }) {
  const locale = await getLocale();
  const counts = analytics.daily_ticket_counts;

  if (counts.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
        <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
          {t(locale, "analytics.volumeHeading")}
        </p>
        <p className="mt-3 text-[13px] text-muted">{t(locale, "analytics.volumeEmpty")}</p>
      </div>
    );
  }

  const total = counts.reduce((sum, c) => sum + c.count, 0);
  const points = buildPoints(counts);
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const areaPath =
    `M${points[0].x.toFixed(1)},${BASELINE} ` +
    points.map((p) => `L${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ") +
    ` L${points[points.length - 1].x.toFixed(1)},${BASELINE} Z`;
  const endpoint = points[points.length - 1];

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
        {t(locale, "analytics.volumeHeading")}
      </p>

      <svg
        className="mt-3 h-auto w-full overflow-visible"
        viewBox={`0 0 ${WIDTH} 130`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="volumeFillGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1={BASELINE - CHART_H * 0.25} x2={WIDTH} y2={BASELINE - CHART_H * 0.25} stroke="var(--border)" />
        <line x1="0" y1={BASELINE - CHART_H * 0.5} x2={WIDTH} y2={BASELINE - CHART_H * 0.5} stroke="var(--border)" />
        <line x1="0" y1={BASELINE - CHART_H * 0.75} x2={WIDTH} y2={BASELINE - CHART_H * 0.75} stroke="var(--border)" />
        <path d={areaPath} fill="url(#volumeFillGrad)" />
        <path
          d={linePath}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <circle cx={endpoint.x} cy={endpoint.y} r="7" fill="none" stroke="var(--accent)" strokeWidth="1.5" opacity="0.4" />
        <circle cx={endpoint.x} cy={endpoint.y} r="3.5" fill="var(--accent)" />
      </svg>

      <p className="mt-2 flex justify-between text-[12px] text-muted">
        <span>{formatDay(counts[0].date, locale)}</span>
        <span className="tabular-nums">{t(locale, "analytics.volumeRange", { total })}</span>
        <span>{formatDay(counts[counts.length - 1].date, locale)}</span>
      </p>
    </div>
  );
}

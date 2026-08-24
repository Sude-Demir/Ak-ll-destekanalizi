import type { Analytics } from "@/lib/api";
import { formatDay } from "@/lib/dateFormat";
import { formatPercent, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const WIDTH = 600;
const BASELINE = 120;
const TOP_PAD = 10;
const CHART_H = BASELINE - TOP_PAD;
const LEFT_PAD = 10;
const RIGHT_PAD = 10;

// Güven skoru zaten 0-1 aralığında sabit bir oran — TicketVolumeChart'taki
// gibi "en yükseğe göre" göreli ölçeklemek yanıltıcı olurdu (dar bir aralıktaki
// %70→%75 sıçraması dev bir artış gibi görünür). Sabit 0-1 ölçek kullanılıyor.
function buildPoints(values: number[]) {
  const stepX = values.length > 1 ? (WIDTH - LEFT_PAD - RIGHT_PAD) / (values.length - 1) : 0;
  return values.map((v, i) => ({
    x: LEFT_PAD + i * stepX,
    y: BASELINE - v * CHART_H,
  }));
}

// Zaman içinde AI performansı düzeliyor mu, kötüleşiyor mu — "canlı bir eval"
// gibi çalışır (bkz. CLAUDE.md "özgün 10 özellik" listesi #9). Ortalama güven
// skoru bir çizgi grafiği olarak (her gün en az bir taslak varsa hep mevcut),
// onay oranı ise ilk/son gün karşılaştırması olarak gösteriliyor (bazı
// günlerde hiç karara bağlanmış taslak olmayabilir — payda 0, oran null).
export default async function DraftTrendChart({ analytics }: { analytics: Analytics }) {
  const locale = await getLocale();
  const points = analytics.draft_trend;

  if (points.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
        <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
          {t(locale, "analytics.trendHeading")}
        </p>
        <p className="mt-3 text-[13px] text-muted">{t(locale, "analytics.trendEmpty")}</p>
      </div>
    );
  }

  const confidenceValues = points.map((p) => p.average_confidence ?? 0);
  const svgPoints = buildPoints(confidenceValues);
  const linePath = svgPoints.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const endpoint = svgPoints[svgPoints.length - 1];

  const rated = points.filter((p) => p.approval_rate !== null);
  const firstRate = rated[0]?.approval_rate ?? null;
  const lastRate = rated[rated.length - 1]?.approval_rate ?? null;

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
        {t(locale, "analytics.trendHeading")}
      </p>
      <p className="mt-1 text-[12.5px] text-muted">{t(locale, "analytics.trendConfidenceLabel")}</p>

      <svg
        className="mt-2 h-auto w-full overflow-visible"
        viewBox={`0 0 ${WIDTH} 130`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <line x1="0" y1={BASELINE - CHART_H * 0.25} x2={WIDTH} y2={BASELINE - CHART_H * 0.25} stroke="var(--border)" />
        <line x1="0" y1={BASELINE - CHART_H * 0.5} x2={WIDTH} y2={BASELINE - CHART_H * 0.5} stroke="var(--border)" />
        <line x1="0" y1={BASELINE - CHART_H * 0.75} x2={WIDTH} y2={BASELINE - CHART_H * 0.75} stroke="var(--border)" />
        <path
          d={linePath}
          fill="none"
          stroke="var(--accent-tech)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <circle cx={endpoint.x} cy={endpoint.y} r="7" fill="none" stroke="var(--accent-tech)" strokeWidth="1.5" opacity="0.4" />
        <circle cx={endpoint.x} cy={endpoint.y} r="3.5" fill="var(--accent-tech)" />
      </svg>

      <p className="mt-2 flex justify-between text-[12px] text-muted">
        <span>{formatDay(points[0].date, locale)}</span>
        <span className="tabular-nums">{formatPercent(confidenceValues[confidenceValues.length - 1], locale)}</span>
        <span>{formatDay(points[points.length - 1].date, locale)}</span>
      </p>

      {firstRate !== null && lastRate !== null && (
        <p className="mt-3 border-t border-border pt-3 text-[12px] text-muted">
          {t(locale, "analytics.trendApprovalChange", {
            first: formatPercent(firstRate, locale),
            last: formatPercent(lastRate, locale),
          })}
        </p>
      )}
    </div>
  );
}

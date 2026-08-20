import { categoryDistribution, categorySwatchClass } from "@/lib/categories";
import { formatPercent, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const TOP_N = 5;

export default async function CategoryDistribution({
  categoryCounts,
  overallTotal,
}: {
  categoryCounts: Record<string, number>;
  overallTotal: number;
}) {
  const total = overallTotal;
  if (total === 0) return null;

  const locale = await getLocale();
  const counts = categoryDistribution(categoryCounts, overallTotal, locale);
  const top = counts.slice(0, TOP_N);
  const otherCount = counts.slice(TOP_N).reduce((sum, c) => sum + c.count, 0);
  // "Diğer" ve "Sınıflandırılmadı" gerçek bir kategori değil; categorySwatchClass
  // bilinmeyen anahtarlar için otomatik olarak nötr griye düşüyor.
  const items =
    otherCount > 0
      ? [...top, { key: "OTHER_GROUP", label: t(locale, "categoryDistribution.other"), count: otherCount }]
      : top;

  return (
    <div className="mt-4 rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
        {t(locale, "categoryDistribution.heading")}
      </p>

      <div className="mt-3 flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden="true">
        {items.map((item) => (
          <div
            key={item.key}
            className={categorySwatchClass(item.key)}
            style={{ width: `${(item.count / total) * 100}%` }}
          />
        ))}
      </div>

      <ul aria-label={t(locale, "categoryDistribution.ariaLabel")} className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
        {items.map((item) => (
          <li key={item.key} className="flex items-center gap-1.5 text-[12px] text-muted">
            <span className={`h-2 w-2 shrink-0 rounded-full ${categorySwatchClass(item.key)}`} aria-hidden="true" />
            {item.label} · {item.count} ({formatPercent(item.count / total, locale)})
          </li>
        ))}
      </ul>
    </div>
  );
}

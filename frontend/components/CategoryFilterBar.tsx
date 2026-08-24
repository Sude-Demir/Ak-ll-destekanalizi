import Link from "next/link";

import { categoryColorClasses, fixedCategoryCounts } from "@/lib/categories";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import { buildDashboardHref } from "@/lib/ticketQuery";

// "Tümü" bir kategori değil, uygulamanın kendi marka vurgusunu (bordo) kullanır.
const ALL_ACTIVE_CLASSES = "border-accent bg-accent text-white";
const ALL_ACTIVE_COUNT_CLASSES = "bg-white/20 text-white";
const INACTIVE_CLASSES = "border-border bg-surface text-muted hover:border-border-strong hover:text-foreground";
const INACTIVE_COUNT_CLASSES = "bg-surface-2 text-faint";

function FilterChip({
  href,
  label,
  count,
  active,
  category,
}: {
  href: string;
  label: string;
  count: number;
  active: boolean;
  /** null = "Tümü" çipi, aksi halde bir kategori kodu. */
  category: string | null;
}) {
  const activeClasses = category ? categoryColorClasses(category) : ALL_ACTIVE_CLASSES;
  const activeCountClasses = category ? "bg-surface text-inherit" : ALL_ACTIVE_COUNT_CLASSES;

  return (
    <Link
      href={href}
      aria-current={active ? "true" : undefined}
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12.5px] font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
        active ? activeClasses : INACTIVE_CLASSES
      }`}
    >
      {label}
      <span
        className={`rounded-full px-1.5 py-0.5 text-[11px] tabular-nums ${
          active ? activeCountClasses : INACTIVE_COUNT_CLASSES
        }`}
      >
        {count}
      </span>
    </Link>
  );
}

/** URL query param'ı (?category=REFUND) üzerinden çalışan, sunucu tarafı bir
 * filtre çubuğu — istemci state'i gerektirmez, sayfa yenilendiğinde veya
 * linki paylaştığında filtre korunur. Sayılar her zaman filtrelenmemiş tam
 * listeden hesaplanır (aktif filtreye göre değişmez), böylece kullanıcı diğer
 * kategorilerde kaç talep olduğunu görebilir. */
export default async function CategoryFilterBar({
  categoryCounts,
  overallTotal,
  activeCategory,
  activeQuery,
  activeAnswered,
  activeChannel,
  activeSort,
  activeLead,
}: {
  categoryCounts: Record<string, number>;
  overallTotal: number;
  activeCategory: string | null;
  activeQuery: string | null;
  activeAnswered: string | null;
  activeChannel: string | null;
  activeSort: string | null;
  activeLead: string | null;
}) {
  const locale = await getLocale();
  const counts = fixedCategoryCounts(categoryCounts, locale);
  const shared = {
    q: activeQuery,
    answered: activeAnswered,
    channel: activeChannel,
    sort: activeSort,
    lead: activeLead,
  };

  return (
    <nav aria-label={t(locale, "categoryFilter.ariaLabel")} className="mt-6">
      <div role="group" className="flex gap-2 overflow-x-auto pb-1.5">
        <FilterChip
          href={buildDashboardHref(shared)}
          label={t(locale, "categoryFilter.all")}
          count={overallTotal}
          active={activeCategory === null}
          category={null}
        />
        {counts.map(({ key, label, count }) => (
          <FilterChip
            key={key}
            href={buildDashboardHref({ ...shared, category: key })}
            label={label}
            count={count}
            active={activeCategory === key}
            category={key}
          />
        ))}
      </div>
    </nav>
  );
}

import Link from "next/link";

import type { Ticket } from "@/lib/api";
import { categoryColorClasses, countsByFixedCategoryOrder } from "@/lib/categories";

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
export default function CategoryFilterBar({
  tickets,
  activeCategory,
}: {
  tickets: Ticket[];
  activeCategory: string | null;
}) {
  const counts = countsByFixedCategoryOrder(tickets);

  return (
    <nav aria-label="Kategoriye göre filtrele" className="mt-6">
      <div role="group" className="flex gap-2 overflow-x-auto pb-1.5">
        <FilterChip
          href="/dashboard"
          label="Tümü"
          count={tickets.length}
          active={activeCategory === null}
          category={null}
        />
        {counts.map(({ key, label, count }) => (
          <FilterChip
            key={key}
            href={`/dashboard?category=${key}`}
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

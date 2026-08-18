import type { Ticket } from "@/lib/api";
import { categorySwatchClass, countTicketsByCategory } from "@/lib/categories";

const TOP_N = 5;

export default function CategoryDistribution({ tickets }: { tickets: Ticket[] }) {
  const total = tickets.length;
  if (total === 0) return null;

  const counts = countTicketsByCategory(tickets);
  const top = counts.slice(0, TOP_N);
  const otherCount = counts.slice(TOP_N).reduce((sum, c) => sum + c.count, 0);
  // "Diğer" ve "Sınıflandırılmadı" gerçek bir kategori değil; categorySwatchClass
  // bilinmeyen anahtarlar için otomatik olarak nötr griye düşüyor.
  const items = otherCount > 0 ? [...top, { key: "OTHER_GROUP", label: "Diğer", count: otherCount }] : top;

  return (
    <div className="mt-4 rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">Kategori Dağılımı</p>

      <div className="mt-3 flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden="true">
        {items.map((item) => (
          <div
            key={item.key}
            className={categorySwatchClass(item.key)}
            style={{ width: `${(item.count / total) * 100}%` }}
          />
        ))}
      </div>

      <ul aria-label="Kategori dağılımı lejantı" className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
        {items.map((item) => (
          <li key={item.key} className="flex items-center gap-1.5 text-[12px] text-muted">
            <span className={`h-2 w-2 shrink-0 rounded-full ${categorySwatchClass(item.key)}`} aria-hidden="true" />
            {item.label} · {item.count} (%{Math.round((item.count / total) * 100)})
          </li>
        ))}
      </ul>
    </div>
  );
}

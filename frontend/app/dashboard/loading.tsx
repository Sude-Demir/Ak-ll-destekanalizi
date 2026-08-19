import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function DashboardLoading() {
  const locale = await getLocale();
  return (
    <main
      className="mx-auto max-w-6xl px-6 py-10"
      aria-busy="true"
      aria-label={t(locale, "dashboard.loadingAriaLabel")}
    >
      <div className="h-[22px] w-56 animate-pulse rounded-md bg-surface-2" />
      <div className="mt-2 h-[13.5px] w-96 animate-pulse rounded-md bg-surface-2" />

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-[68px] animate-pulse rounded-xl border border-border bg-surface-2" />
        ))}
      </div>

      <div className="mt-4 h-[104px] animate-pulse rounded-xl border border-border bg-surface-2" />

      <div className="mt-6 flex gap-2 overflow-hidden">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-[30px] w-24 shrink-0 animate-pulse rounded-full bg-surface-2" />
        ))}
      </div>

      <div className="mt-6 overflow-hidden rounded-xl border border-border">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-[54px] animate-pulse border-b border-border bg-surface-2 last:border-b-0"
            style={{ animationDelay: `${i * 75}ms` }}
          />
        ))}
      </div>
    </main>
  );
}

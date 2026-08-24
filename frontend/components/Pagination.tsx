import Link from "next/link";

import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import { buildDashboardHref } from "@/lib/ticketQuery";

export default async function Pagination({
  page,
  pageSize,
  total,
  category,
  query,
  answered,
  channel,
  sort,
  lead,
}: {
  page: number;
  pageSize: number;
  total: number;
  category: string | null;
  query: string | null;
  answered: string | null;
  channel: string | null;
  sort: string | null;
  lead: string | null;
}) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  const locale = await getLocale();
  const shared = { category, q: query, answered, channel, sort, lead };
  const linkClasses =
    "rounded-lg border border-border px-3 py-1.5 text-[12.5px] font-semibold text-muted hover:border-border-strong hover:text-foreground";

  return (
    <nav aria-label={t(locale, "pagination.ariaLabel")} className="mt-4 flex items-center justify-center gap-1.5">
      {page > 1 ? (
        <Link href={buildDashboardHref({ ...shared, page: page - 1 })} className={linkClasses}>
          {t(locale, "pagination.previous")}
        </Link>
      ) : (
        <span className={`${linkClasses} pointer-events-none opacity-40`}>{t(locale, "pagination.previous")}</span>
      )}
      <span className="px-2 text-[12.5px] tabular-nums text-muted">
        {t(locale, "pagination.pageOf", { page, totalPages })}
      </span>
      {page < totalPages ? (
        <Link href={buildDashboardHref({ ...shared, page: page + 1 })} className={linkClasses}>
          {t(locale, "pagination.next")}
        </Link>
      ) : (
        <span className={`${linkClasses} pointer-events-none opacity-40`}>{t(locale, "pagination.next")}</span>
      )}
    </nav>
  );
}

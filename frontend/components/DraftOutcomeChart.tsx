import type { Analytics } from "@/lib/api";
import { DRAFT_STATUS_LABEL_KEYS, DRAFT_STATUS_SWATCH_CLASSES } from "@/lib/draftStatus";
import { formatPercent, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const STATUS_ORDER = ["approved", "edited", "pending", "rejected"] as const;

export default async function DraftOutcomeChart({ analytics }: { analytics: Analytics }) {
  const locale = await getLocale();
  const { drafts } = analytics;
  const total = drafts.total;

  if (total === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
        <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
          {t(locale, "analytics.draftOutcomeHeading")}
        </p>
        <p className="mt-3 text-[13px] text-muted">{t(locale, "analytics.draftOutcomeEmpty")}</p>
      </div>
    );
  }

  const items = STATUS_ORDER.map((status) => ({
    key: status,
    label: t(locale, DRAFT_STATUS_LABEL_KEYS[status]),
    count: drafts[status],
  })).filter((item) => item.count > 0);

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
        {t(locale, "analytics.draftOutcomeHeading")}
      </p>

      <div className="mt-3 flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden="true">
        {items.map((item) => (
          <div
            key={item.key}
            className={DRAFT_STATUS_SWATCH_CLASSES[item.key]}
            style={{ width: `${(item.count / total) * 100}%` }}
          />
        ))}
      </div>

      <ul
        aria-label={t(locale, "analytics.draftOutcomeAriaLabel")}
        className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5"
      >
        {items.map((item) => (
          <li key={item.key} className="flex items-center gap-1.5 text-[12px] text-muted">
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${DRAFT_STATUS_SWATCH_CLASSES[item.key]}`}
              aria-hidden="true"
            />
            {item.label} · {item.count} ({formatPercent(item.count / total, locale)})
          </li>
        ))}
      </ul>

      {drafts.escalated > 0 && (
        <p className="mt-3 border-t border-border pt-3 text-[12px] text-muted">
          {t(locale, "analytics.escalatedCount", { count: drafts.escalated })}
        </p>
      )}
    </div>
  );
}

import CategoryBadge from "@/components/CategoryBadge";
import type { KnowledgeGap } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

// Bir şirketin hangi kategorilerde SSS'inin muhtemelen eksik olduğunu
// gösterir — AI'nin sık sık düşük güvenle/eskalasyona düşerek taslak
// ürettiği kategoriler (bkz. backend/app/routers/analytics.py _knowledge_gaps).
export default async function KnowledgeGaps({ gaps }: { gaps: KnowledgeGap[] }) {
  const locale = await getLocale();

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-[11.5px] font-bold tracking-wide text-faint uppercase">
        {t(locale, "analytics.knowledgeGapsHeading")}
      </p>
      <p className="mt-1.5 text-[12.5px] text-muted">{t(locale, "analytics.knowledgeGapsSubtitle")}</p>

      {gaps.length === 0 ? (
        <p className="mt-3 text-[13px] text-muted">{t(locale, "analytics.knowledgeGapsEmpty")}</p>
      ) : (
        <ul className="mt-3.5 space-y-3">
          {gaps.map((gap) => (
            <li key={gap.category} className="rounded-lg border border-border bg-surface-2 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CategoryBadge category={gap.category} locale={locale} />
                <span className="text-[12px] font-semibold tabular-nums text-muted">
                  {t(locale, "analytics.knowledgeGapsEscalatedOf", {
                    escalated: gap.escalated_count,
                    total: gap.total_count,
                  })}
                </span>
              </div>
              {gap.sample_subjects.length > 0 && (
                <div className="mt-2.5 border-t border-border pt-2.5">
                  <p className="text-[10.5px] font-bold tracking-wide text-faint uppercase">
                    {t(locale, "analytics.knowledgeGapsSamplesHeading")}
                  </p>
                  <ul className="mt-1.5 space-y-1">
                    {gap.sample_subjects.map((subject, i) => (
                      <li key={i} className="truncate text-[12.5px] text-muted">
                        {subject}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

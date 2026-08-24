import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

import AnalyticsHero from "@/components/AnalyticsHero";
import DraftOutcomeChart from "@/components/DraftOutcomeChart";
import DraftTrendChart from "@/components/DraftTrendChart";
import KnowledgeGaps from "@/components/KnowledgeGaps";
import TicketVolumeChart from "@/components/TicketVolumeChart";
import { fetchAnalytics, fetchKnowledgeGaps } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function AnalyticsPage() {
  const locale = await getLocale();
  const { getToken } = await auth();
  const token = await getToken();

  let analytics;
  let knowledgeGaps;
  let errorMessage: string | null = null;

  try {
    [analytics, knowledgeGaps] = await Promise.all([fetchAnalytics(token), fetchKnowledgeGaps(token)]);
  } catch (error) {
    // Backend, temsilci olmayan bir kullanıcı için 403 döner (bkz.
    // backend/app/auth.py require_agent) — bu bir hata değil, kişi müşteri
    // portalına ait demektir (bkz. app/dashboard/page.tsx aynı desen).
    if (error instanceof Error && error.message.includes("403")) {
      redirect("/portal");
    }
    errorMessage = t(locale, "analytics.loadError");
  }

  if (errorMessage) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-red-600">{errorMessage}</p>
      </main>
    );
  }

  if (!analytics || !knowledgeGaps) return null;

  return (
    <>
      <AnalyticsHero analytics={analytics} />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="grid gap-4 sm:grid-cols-2">
          <DraftOutcomeChart analytics={analytics} />
          <TicketVolumeChart analytics={analytics} />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <DraftTrendChart analytics={analytics} />
          <KnowledgeGaps gaps={knowledgeGaps} />
        </div>
      </main>
    </>
  );
}

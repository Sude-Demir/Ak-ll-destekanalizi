import type { Locale } from "@/lib/i18n";

// Backend tarih-only (YYYY-MM-DD) döner, formatDate'in (lib/i18n.ts) timeStyle'ı
// burada gereksiz — sadece gün/ay göstermek yeterli. TicketVolumeChart ve
// AnalyticsHero ikisi de kullanır.
export function formatDay(isoDate: string, locale: Locale): string {
  return new Date(isoDate).toLocaleDateString(locale === "tr" ? "tr-TR" : "en-US", {
    day: "numeric",
    month: "short",
  });
}

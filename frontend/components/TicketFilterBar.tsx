import Link from "next/link";

import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import { buildDashboardHref } from "@/lib/ticketQuery";

const ACTIVE_CLASSES = "border-accent bg-accent text-white";
const INACTIVE_CLASSES = "border-border bg-surface text-muted hover:border-border-strong hover:text-foreground";

function Chip({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <Link
      href={href}
      aria-current={active ? "true" : undefined}
      className={`inline-flex shrink-0 items-center rounded-full border px-3 py-1 text-[12.5px] font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
        active ? ACTIVE_CLASSES : INACTIVE_CLASSES
      }`}
    >
      {label}
    </Link>
  );
}

// Aşağı ok = en yeni önce (varsayılan), yukarı ok (180° döndürülmüş) = en
// eski önce — ThemeSwitcher.tsx'teki gibi kütüphanesiz, inline SVG.
function SortIcon({ ascending }: { ascending: boolean }) {
  return (
    <svg
      viewBox="0 0 16 16"
      className={`h-3.5 w-3.5 shrink-0 transition-transform ${ascending ? "rotate-180" : ""}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
    >
      <path d="M8 2.5v11M8 13.5 4.5 10M8 13.5 11.5 10" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// "twitter" seed veride (Kaggle ingest, scripts/ingest_kaggle_tickets.py) 300
// talebin tamamının kanalı — email/form/portal ise sonradan eklenen gerçek
// giriş yolları (bkz. CLAUDE.md "Mevcut Aşama"). Dördü de burada listeleniyor.
const CHANNELS = ["twitter", "email", "form", "portal"] as const;

const CHANNEL_LABEL_KEYS = {
  twitter: "ticketFilterBar.channelTwitter",
  email: "ticketFilterBar.channelEmail",
  form: "ticketFilterBar.channelForm",
  portal: "ticketFilterBar.channelPortal",
} as const;

/** Cevap durumu, kanal, lead ve sıralama için CategoryFilterBar'a paralel
 * çalışan, URL query-state'i (?answered=&channel=&lead=&sort=) üzerinden
 * işleyen ikinci bir filtre çubuğu — istemci state'i gerektirmez.
 * CategoryFilterBar zaten kategoriyi ve sayıları gösterdiği için burada
 * sadece bu yeni boyutlara yer verilir, kategori/arama aktif değeri sadece
 * diğer filtreler değişince korunsun diye taşınır (bkz. buildDashboardHref).
 * Her chip/link, DEĞİŞTİRMEDİĞİ diğer tüm boyutları da elden geçirip iletir
 * — aksi halde örn. kanal seçmek lead filtresini sessizce sıfırlardı. */
export default async function TicketFilterBar({
  activeCategory,
  activeQuery,
  activeAnswered,
  activeChannel,
  activeSort,
  activeLead,
}: {
  activeCategory: string | null;
  activeQuery: string | null;
  activeAnswered: string | null;
  activeChannel: string | null;
  activeSort: string | null;
  activeLead: string | null;
}) {
  const locale = await getLocale();
  const shared = { category: activeCategory, q: activeQuery };
  const isOldest = activeSort === "oldest";

  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2">
      <nav aria-label={t(locale, "ticketFilterBar.answeredAriaLabel")} className="flex items-center gap-1.5">
        <span className="text-[12px] font-semibold text-faint">{t(locale, "ticketsTable.answer")}</span>
        <Chip
          href={buildDashboardHref({ ...shared, channel: activeChannel, sort: activeSort, lead: activeLead })}
          label={t(locale, "categoryFilter.all")}
          active={activeAnswered === null}
        />
        <Chip
          href={buildDashboardHref({
            ...shared,
            channel: activeChannel,
            sort: activeSort,
            lead: activeLead,
            answered: "true",
          })}
          label={t(locale, "ticketsTable.answered")}
          active={activeAnswered === "true"}
        />
        <Chip
          href={buildDashboardHref({
            ...shared,
            channel: activeChannel,
            sort: activeSort,
            lead: activeLead,
            answered: "false",
          })}
          label={t(locale, "ticketsTable.unanswered")}
          active={activeAnswered === "false"}
        />
      </nav>

      <nav aria-label={t(locale, "ticketFilterBar.channelAriaLabel")} className="flex items-center gap-1.5">
        <span className="text-[12px] font-semibold text-faint">{t(locale, "ticketsTable.channel")}</span>
        <Chip
          href={buildDashboardHref({ ...shared, answered: activeAnswered, sort: activeSort, lead: activeLead })}
          label={t(locale, "categoryFilter.all")}
          active={activeChannel === null}
        />
        {CHANNELS.map((channel) => (
          <Chip
            key={channel}
            href={buildDashboardHref({
              ...shared,
              answered: activeAnswered,
              sort: activeSort,
              lead: activeLead,
              channel,
            })}
            label={t(locale, CHANNEL_LABEL_KEYS[channel])}
            active={activeChannel === channel}
          />
        ))}
      </nav>

      <nav aria-label={t(locale, "ticketFilterBar.leadAriaLabel")} className="flex items-center gap-1.5">
        <span className="text-[12px] font-semibold text-faint">{t(locale, "ticketFilterBar.leadLabel")}</span>
        <Chip
          href={buildDashboardHref({ ...shared, answered: activeAnswered, channel: activeChannel, sort: activeSort })}
          label={t(locale, "categoryFilter.all")}
          active={activeLead === null}
        />
        <Chip
          href={buildDashboardHref({
            ...shared,
            answered: activeAnswered,
            channel: activeChannel,
            sort: activeSort,
            lead: "true",
          })}
          label={t(locale, "ticketFilterBar.leadOnly")}
          active={activeLead === "true"}
        />
      </nav>

      <Link
        href={buildDashboardHref({
          ...shared,
          answered: activeAnswered,
          channel: activeChannel,
          lead: activeLead,
          sort: isOldest ? null : "oldest",
        })}
        aria-label={t(locale, "ticketFilterBar.sortAriaLabel")}
        title={t(locale, "ticketFilterBar.sortAriaLabel")}
        className="ml-auto inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-[12.5px] font-semibold text-muted transition-colors hover:border-border-strong hover:text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <SortIcon ascending={isOldest} />
        {t(locale, isOldest ? "ticketFilterBar.sortOldest" : "ticketFilterBar.sortNewest")}
      </Link>
    </div>
  );
}

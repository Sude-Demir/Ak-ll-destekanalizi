"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { useLocale } from "@/components/LocaleProvider";
import type { TranslationKey } from "@/lib/i18n";
import { buildDashboardHref } from "@/lib/ticketQuery";

// "twitter" seed veride (Kaggle ingest, scripts/ingest_kaggle_tickets.py) 300
// talebin tamamının kanalı — email/form/portal ise sonradan eklenen gerçek
// giriş yolları (bkz. CLAUDE.md "Mevcut Aşama"). Dördü de burada listeleniyor.
const CHANNELS = ["twitter", "email", "form", "portal"] as const;

const CHANNEL_LABEL_KEYS: Record<(typeof CHANNELS)[number], TranslationKey> = {
  twitter: "ticketFilterBar.channelTwitter",
  email: "ticketFilterBar.channelEmail",
  form: "ticketFilterBar.channelForm",
  portal: "ticketFilterBar.channelPortal",
};

function FilterSelect({
  label,
  ariaLabel,
  value,
  onChange,
  children,
}: {
  label: string;
  ariaLabel: string;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <label className="flex items-center gap-1.5 text-[12.5px]">
      <span className="font-semibold text-faint">{label}</span>
      <select
        aria-label={ariaLabel}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-border bg-surface py-1.5 pl-2 pr-1 text-[12.5px] font-medium text-foreground focus:border-accent focus:outline-none"
      >
        {children}
      </select>
    </label>
  );
}

type DashboardHrefParams = Parameters<typeof buildDashboardHref>[0];

/** Cevap durumu, kanal, lead, aciliyet ve sıralama için CategoryFilterBar'a
 * paralel çalışan, URL query-state'i (?answered=&channel=&lead=&urgent=&sort=)
 * üzerinden işleyen ikinci bir filtre çubuğu. Beş ayrı boyutu tek tek chip
 * satırları yerine kompakt dropdown'lar olarak gösterir (kullanıcı geri
 * bildirimi: eski chip düzeni "aşırı düzensiz" duruyordu, satır satır
 * taşıp yatay kaydırma gerektiriyordu) — bu yüzden client component'e
 * çevrildi (`router.push`, bkz. SearchBox.tsx ile aynı URL-state deseni). */
export default function TicketFilterBar({
  activeCategory,
  activeQuery,
  activeAnswered,
  activeChannel,
  activeSort,
  activeLead,
  activeUrgent,
}: {
  activeCategory: string | null;
  activeQuery: string | null;
  activeAnswered: string | null;
  activeChannel: string | null;
  activeSort: string | null;
  activeLead: string | null;
  activeUrgent: string | null;
}) {
  const router = useRouter();
  const { t } = useLocale();

  function go(overrides: Partial<DashboardHrefParams>) {
    router.push(
      buildDashboardHref({
        category: activeCategory,
        q: activeQuery,
        answered: activeAnswered,
        channel: activeChannel,
        sort: activeSort,
        lead: activeLead,
        urgent: activeUrgent,
        ...overrides,
      })
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-border bg-surface-2 px-3.5 py-2.5">
      <FilterSelect
        label={t("ticketsTable.answer")}
        ariaLabel={t("ticketFilterBar.answeredAriaLabel")}
        value={activeAnswered ?? "all"}
        onChange={(v) => go({ answered: v === "all" ? null : v })}
      >
        <option value="all">{t("categoryFilter.all")}</option>
        <option value="true">{t("ticketsTable.answered")}</option>
        <option value="false">{t("ticketsTable.unanswered")}</option>
      </FilterSelect>

      <FilterSelect
        label={t("ticketsTable.channel")}
        ariaLabel={t("ticketFilterBar.channelAriaLabel")}
        value={activeChannel ?? "all"}
        onChange={(v) => go({ channel: v === "all" ? null : v })}
      >
        <option value="all">{t("categoryFilter.all")}</option>
        {CHANNELS.map((channel) => (
          <option key={channel} value={channel}>
            {t(CHANNEL_LABEL_KEYS[channel])}
          </option>
        ))}
      </FilterSelect>

      <FilterSelect
        label={t("ticketFilterBar.leadLabel")}
        ariaLabel={t("ticketFilterBar.leadAriaLabel")}
        value={activeLead ?? "all"}
        onChange={(v) => go({ lead: v === "all" ? null : v })}
      >
        <option value="all">{t("categoryFilter.all")}</option>
        <option value="true">{t("ticketFilterBar.leadOnly")}</option>
      </FilterSelect>

      <FilterSelect
        label={t("ticketFilterBar.urgentLabel")}
        ariaLabel={t("ticketFilterBar.urgentAriaLabel")}
        value={activeUrgent ?? "all"}
        onChange={(v) => go({ urgent: v === "all" ? null : v })}
      >
        <option value="all">{t("categoryFilter.all")}</option>
        <option value="true">{t("ticketFilterBar.urgentOnly")}</option>
      </FilterSelect>

      <FilterSelect
        label={t("ticketFilterBar.sortLabel")}
        ariaLabel={t("ticketFilterBar.sortAriaLabel")}
        value={activeSort ?? "newest"}
        onChange={(v) => go({ sort: v === "newest" ? null : v })}
      >
        <option value="newest">{t("ticketFilterBar.sortNewest")}</option>
        <option value="oldest">{t("ticketFilterBar.sortOldest")}</option>
        <option value="priority">{t("ticketFilterBar.sortPriority")}</option>
      </FilterSelect>
    </div>
  );
}

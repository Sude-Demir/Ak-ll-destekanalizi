"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useLocale } from "@/components/LocaleProvider";
import type { TranslationKey } from "@/lib/i18n";

function TicketsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 6h16M4 12h16M4 18h10" strokeLinecap="round" />
    </svg>
  );
}

function AnalyticsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 20V10M12 20V4M20 20v-7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TeamIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="9" cy="8" r="3" />
      <path d="M2 20c0-3.3 3.1-6 7-6s7 2.7 7 6M17 8.5c1.7.3 3 1.6 3 3.2M21 20c0-2.2-1.6-4.1-4-5" strokeLinecap="round" />
    </svg>
  );
}

const NAV_ITEMS = [
  { href: "/dashboard", labelKey: "sidebar.tickets" as TranslationKey, icon: TicketsIcon },
  { href: "/dashboard/analytics", labelKey: "dashboard.analytics" as TranslationKey, icon: AnalyticsIcon },
  { href: "/dashboard/team", labelKey: "dashboard.team" as TranslationKey, icon: TeamIcon },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/dashboard") {
    return pathname === "/dashboard" || pathname.startsWith("/dashboard/tickets");
  }
  return pathname.startsWith(href);
}

export default function DashboardSidebar() {
  const pathname = usePathname();
  const { t } = useLocale();

  return (
    <nav className="flex shrink-0 gap-1 overflow-x-auto border-b border-border bg-surface-2 p-2.5 md:sticky md:top-14 md:w-56 md:max-h-[calc(100vh-56px)] md:flex-col md:self-start md:overflow-y-auto md:border-b-0 md:border-r md:p-4">
      {NAV_ITEMS.map(({ href, labelKey, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] font-semibold whitespace-nowrap ${
              active ? "bg-accent-soft text-accent" : "text-muted hover:bg-surface hover:text-foreground"
            }`}
          >
            <span className={`h-4 w-4 shrink-0 ${active ? "opacity-100" : "opacity-70"}`}>
              <Icon />
            </span>
            {t(labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}

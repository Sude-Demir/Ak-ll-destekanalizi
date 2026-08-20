"use client";

import { useLocale } from "@/components/LocaleProvider";
import { useTheme } from "@/components/ThemeProvider";
import type { TranslationKey } from "@/lib/i18n";
import type { Theme } from "@/lib/theme";

function SystemIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.3">
      <rect x="1.5" y="2.5" width="13" height="8.5" rx="1" />
      <path d="M5.5 14h5M8 11v3" strokeLinecap="round" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.3">
      <circle cx="8" cy="8" r="3" />
      <path
        d="M8 1v1.5M8 13.5V15M15 8h-1.5M2.5 8H1M12.7 3.3l-1 1M4.3 11.7l-1 1M12.7 12.7l-1-1M4.3 4.3l-1-1"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.3">
      <path d="M13.5 9.5A5.5 5.5 0 0 1 6.5 2.5a5.5 5.5 0 1 0 7 7Z" strokeLinejoin="round" />
    </svg>
  );
}

const OPTIONS = [
  { value: "system" as Theme, Icon: SystemIcon, labelKey: "theme.system" as TranslationKey },
  { value: "light" as Theme, Icon: SunIcon, labelKey: "theme.light" as TranslationKey },
  { value: "dark" as Theme, Icon: MoonIcon, labelKey: "theme.dark" as TranslationKey },
];

export default function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  const { t } = useLocale();

  return (
    <div
      role="group"
      aria-label={t("theme.switcherLabel")}
      className="flex items-center gap-0.5 rounded-lg border border-border bg-surface-2 p-0.5"
    >
      {OPTIONS.map(({ value, Icon, labelKey }) => (
        <button
          key={value}
          type="button"
          onClick={() => setTheme(value)}
          aria-current={theme === value}
          aria-label={t(labelKey)}
          title={t(labelKey)}
          className={`flex items-center justify-center rounded-md p-1.5 transition-colors ${
            theme === value ? "bg-accent text-white" : "text-muted hover:text-foreground"
          }`}
        >
          <Icon />
        </button>
      ))}
    </div>
  );
}

"use client";

import { useLocale } from "@/components/LocaleProvider";

const OPTIONS = [
  { value: "tr", label: "TR" },
  { value: "en", label: "EN" },
] as const;

export default function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();

  return (
    <div role="group" aria-label="Dil / Language" className="flex items-center gap-0.5 rounded-lg border border-border bg-surface-2 p-0.5">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => setLocale(option.value)}
          aria-current={locale === option.value}
          className={`rounded-md px-2 py-1 text-[11.5px] font-bold tracking-wide transition-colors ${
            locale === option.value
              ? "bg-accent text-white"
              : "text-muted hover:text-foreground"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

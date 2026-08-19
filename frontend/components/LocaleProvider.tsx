"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useState, type ReactNode } from "react";

import { LOCALE_COOKIE, t as translate, type Locale, type TranslationKey } from "@/lib/i18n";

interface LocaleContextValue {
  locale: Locale;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
  setLocale: (locale: Locale) => void;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365; // 1 yıl

/** `initialLocale`, sunucuda (app/layout.tsx) cookie'den okunur — böylece
 * ilk render'da bile doğru dil gösterilir, kısa süreliğine yanlış dilde
 * "flash" yaşanmaz. */
export function LocaleProvider({ initialLocale, children }: { initialLocale: Locale; children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale);
  const router = useRouter();

  function setLocale(next: Locale) {
    setLocaleState(next);
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=${COOKIE_MAX_AGE_SECONDS}`;
    // Server component'ler (dashboard, portal, vb.) yeni cookie'yle yeniden
    // render olsun diye.
    router.refresh();
  }

  return (
    <LocaleContext.Provider
      value={{ locale, t: (key, params) => translate(locale, key, params), setLocale }}
    >
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error("useLocale, bir LocaleProvider içinde kullanılmalı");
  }
  return ctx;
}

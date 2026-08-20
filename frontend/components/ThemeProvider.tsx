"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useState, type ReactNode } from "react";

import { THEME_COOKIE, type Theme } from "@/lib/theme";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365; // 1 yıl

/** `LocaleProvider.tsx` ile birebir aynı iskelet — cookie + `router.refresh()`.
 * Tema bilgisi bilinçli olarak `localStorage` değil cookie'de tutuluyor:
 * `app/layout.tsx` server-side `getTheme()` ile okuyup `<html data-theme>`'i
 * İLK render'da doğru üretiyor, bu yüzden client-side bir "flash önleme"
 * script'ine hiç gerek kalmıyor (önceki `next/script beforeInteractive`
 * denemesi React 19'un script-hoisting davranışıyla çakışıyordu — bu daha
 * basit ve daha az kırılgan bir çözüm). */
export function ThemeProvider({ initialTheme, children }: { initialTheme: Theme; children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(initialTheme);
  const router = useRouter();

  function setTheme(next: Theme) {
    setThemeState(next);
    document.cookie = `${THEME_COOKIE}=${next}; path=/; max-age=${COOKIE_MAX_AGE_SECONDS}`;
    // <html data-theme> app/layout.tsx'te (server component) render ediliyor —
    // server component'ler yeni cookie'yle yeniden render olsun diye.
    router.refresh();
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme, bir ThemeProvider içinde kullanılmalı");
  }
  return ctx;
}

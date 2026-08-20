import { ClerkProvider } from "@clerk/nextjs";
import { enUS, trTR } from "@clerk/localizations";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import AppBar from "@/components/AppBar";
import { LocaleProvider } from "@/components/LocaleProvider";
import { ThemeProvider } from "@/components/ThemeProvider";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import { getTheme } from "@/lib/theme-server";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  return {
    // Ürün adı bir marka ismi — dile göre çevrilmiyor, sabit kalıyor.
    title: "Akıllı Destek Asistanı",
    description: t(locale, "meta.description"),
  };
}

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const locale = await getLocale();
  const theme = await getTheme();

  return (
    <ClerkProvider
      localization={locale === "tr" ? trTR : enUS}
      afterSignOutUrl="/sign-in"
      appearance={{
        variables: {
          colorPrimary: "var(--accent)",
          colorBackground: "var(--surface)",
          colorForeground: "var(--foreground)",
          colorMutedForeground: "var(--muted)",
          colorInput: "var(--surface-2)",
          colorInputForeground: "var(--foreground)",
          borderRadius: "0.75rem",
        },
        elements: {
          // Kullanıcı menüsündeki "Hesabı yönet" / "Çıkış yap" gibi eylem
          // butonları varsayılan olarak çok soluk (muted) renk kullanıyor,
          // koyu zeminde neredeyse okunmuyordu — okunur kontrasta sabitledik.
          userButtonPopoverActionButton: { color: "var(--foreground)" },
          userButtonPopoverActionButtonIcon: { color: "var(--foreground)" },
        },
      }}
    >
      <html
        lang={locale}
        // "system" için attribute hiç eklenmiyor (React, undefined attribute'u
        // atlar) — globals.css'teki prefers-color-scheme media query'si
        // devreye girsin diye. Cookie'den server-side okunduğu için (bkz.
        // lib/theme-server.ts) ilk render'dan itibaren doğru — client-side bir
        // "flash önleme" script'ine hiç gerek yok.
        data-theme={theme === "system" ? undefined : theme}
        className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      >
        <body className="min-h-full flex flex-col bg-background text-foreground">
          <ThemeProvider initialTheme={theme}>
            <LocaleProvider initialLocale={locale}>
              <AppBar />
              {children}
            </LocaleProvider>
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}

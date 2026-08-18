import { ClerkProvider } from "@clerk/nextjs";
import { trTR } from "@clerk/localizations";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import AppBar from "@/components/AppBar";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Akıllı Destek Asistanı",
  description: "Müşteri destek taleplerini yöneten iç panel",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <ClerkProvider
      localization={trTR}
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
        lang="tr"
        className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      >
        <body className="min-h-full flex flex-col bg-background text-foreground">
          <AppBar />
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}

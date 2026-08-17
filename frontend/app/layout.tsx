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
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <AppBar />
        {children}
      </body>
    </html>
  );
}

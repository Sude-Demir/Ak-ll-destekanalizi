import type { Locale } from "@/lib/i18n";

// tickets.status için etiket/renk sözlükleri. TicketsTable.tsx (client
// component) ve talep detay sayfası (server component) ikisi de kullanıyor —
// "use client" işaretli bir dosyadan sabit export etmek RSC derleyicisinde
// server component'lerin okuyamayacağı bir client-reference'a dönüşüyor, bu
// yüzden paylaşılan sabitler ayrı, "use client" İÇERMEYEN bu dosyada duruyor.
export const TICKET_STATUS_LABELS: Record<Locale, Record<string, string>> = {
  tr: { open: "Açık", pending: "Beklemede", closed: "Kapalı" },
  en: { open: "Open", pending: "Pending", closed: "Closed" },
};

export const TICKET_STATUS_STYLES: Record<string, string> = {
  open: "bg-status-open-bg text-status-open-fg",
  pending: "bg-status-wait-bg text-status-wait-fg",
  closed: "bg-status-done-bg text-status-done-fg",
};

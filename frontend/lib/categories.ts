import { t, type Locale } from "@/lib/i18n";

// Kaynak liste: backend/app/services/classification.py CATEGORIES. Backend'e
// dokunmadan filtre çubuğunda sabit ve öngörülebilir bir sırayla göstermek için
// burada ayrıca tutuluyor.
export const CATEGORIES = [
  "ACCOUNT",
  "ORDER",
  "REFUND",
  "DELIVERY",
  "PAYMENT",
  "INVOICE",
  "SHIPPING",
  "CANCEL",
  "CONTACT",
  "FEEDBACK",
  "SUBSCRIPTION",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<Locale, Record<Category, string>> = {
  tr: {
    ACCOUNT: "Hesap",
    ORDER: "Sipariş",
    REFUND: "İade",
    DELIVERY: "Teslimat",
    PAYMENT: "Ödeme",
    INVOICE: "Fatura",
    SHIPPING: "Kargo",
    CANCEL: "İptal",
    CONTACT: "İletişim",
    FEEDBACK: "Geri Bildirim",
    SUBSCRIPTION: "Abonelik",
  },
  en: {
    ACCOUNT: "Account",
    ORDER: "Order",
    REFUND: "Refund",
    DELIVERY: "Delivery",
    PAYMENT: "Payment",
    INVOICE: "Invoice",
    SHIPPING: "Shipping",
    CANCEL: "Cancellation",
    CONTACT: "Contact",
    FEEDBACK: "Feedback",
    SUBSCRIPTION: "Subscription",
  },
};

export const UNCLASSIFIED_KEY = "UNCLASSIFIED";

export function isCategory(value: string): value is Category {
  return (CATEGORIES as readonly string[]).includes(value);
}

// Küçük, tekrar eden bir renk paleti (bkz. app/globals.css --category-a..f).
// 11 kategoriye 11 ayrı renk vermek yerine 6 rengi CATEGORIES sırasına göre
// döngüsel dağıtıyoruz — bazı kategoriler aynı rengi paylaşır. Sıralama
// bilinçli: ORDER 2. sırada olduğu için "b" (kırmızı), REFUND 3. sırada
// olduğu için "c" (mavi) alıyor.
const CATEGORY_PALETTE = ["a", "b", "c", "d", "e", "f"] as const;
type PaletteKey = (typeof CATEGORY_PALETTE)[number];

const CATEGORY_COLOR: Record<Category, PaletteKey> = Object.fromEntries(
  CATEGORIES.map((cat, i) => [cat, CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]])
) as Record<Category, PaletteKey>;

const NEUTRAL_SWATCH_CLASS = "bg-border-strong";
const NEUTRAL_BADGE_CLASSES = "border-border-strong bg-surface-2 text-faint";

// Tailwind, kullanılan class'ları KAYNAK KODUNU STATİK OLARAK TARAYARAK bulur
// (JS'i çalıştırmaz) — `` `bg-category-${key}-bg` `` gibi template literal'lerle
// birleştirilen class isimlerini ASLA üretmez. Bu yüzden her palet harfi için
// tam class string'lerini burada, harfiyen yazılmış olarak tutuyoruz.
const BADGE_CLASSES: Record<PaletteKey, string> = {
  a: "border-category-a-fg bg-category-a-bg text-category-a-fg",
  b: "border-category-b-fg bg-category-b-bg text-category-b-fg",
  c: "border-category-c-fg bg-category-c-bg text-category-c-fg",
  d: "border-category-d-fg bg-category-d-bg text-category-d-fg",
  e: "border-category-e-fg bg-category-e-bg text-category-e-fg",
  f: "border-category-f-fg bg-category-f-bg text-category-f-fg",
};

const SWATCH_CLASSES: Record<PaletteKey, string> = {
  a: "bg-category-a-fg",
  b: "bg-category-b-fg",
  c: "bg-category-c-fg",
  d: "bg-category-d-fg",
  e: "bg-category-e-fg",
  f: "bg-category-f-fg",
};

/** Rozet/aktif filtre çipi için: yumuşak arka plan + okunur metin + aynı
 * tondan kenarlık. `category` bilinmeyen bir değerse (örn. backend'in
 * FALLBACK_CATEGORY'si "OTHER") nötr bir stile düşer. */
export function categoryColorClasses(category: string): string {
  if (!isCategory(category)) return NEUTRAL_BADGE_CLASSES;
  return BADGE_CLASSES[CATEGORY_COLOR[category]];
}

/** Dağılım çubuğu/lejant noktası gibi tek renkli, dolgun bir yüzey için. */
export function categorySwatchClass(key: string): string {
  if (key === UNCLASSIFIED_KEY || !isCategory(key)) return NEUTRAL_SWATCH_CLASS;
  return SWATCH_CLASSES[CATEGORY_COLOR[key]];
}

/** `key`, gerçek bir kategori kodu ya da UNCLASSIFIED_KEY olabilir. Backend'in
 * FALLBACK_CATEGORY'si ("OTHER") gibi bilinmeyen değerler ham haliyle döner. */
export function categoryLabel(key: string, locale: Locale): string {
  if (key === UNCLASSIFIED_KEY) return t(locale, "category.unclassified");
  return isCategory(key) ? CATEGORY_LABELS[locale][key] : key;
}

export interface CategoryCount {
  key: string;
  label: string;
  count: number;
}

// Backend'in GET /tickets yanıtındaki category_counts alanından besleniyor
// (bkz. backend/app/schemas.py TicketListRead) — arama/kategori filtresinden
// BAĞIMSIZ, şirketin TÜM talepleri üzerinden hesaplanmış sayılar. Bu yüzden
// tickets.length yerine ayrıca `overallTotal` parametre olarak alınıyor.

/** 11 sabit kategoriyi (0 sayılı olsa bile) her zaman aynı sırada döner —
 * filtre çubuğunun her yüklemede aynı düzende görünmesi için. */
export function fixedCategoryCounts(categoryCounts: Record<string, number>, locale: Locale): CategoryCount[] {
  return CATEGORIES.map((key) => ({ key, label: CATEGORY_LABELS[locale][key], count: categoryCounts[key] ?? 0 }));
}

/** Talep sayısına göre azalan sırada, sınıflandırılmamış talepleri de ayrı bir
 * grup olarak dahil eder (overallTotal - sınıflandırılmış toplam). Dağılım
 * özetinde kullanılır. */
export function categoryDistribution(
  categoryCounts: Record<string, number>,
  overallTotal: number,
  locale: Locale
): CategoryCount[] {
  const entries = Object.entries(categoryCounts).filter(([, count]) => count > 0);
  const classifiedTotal = entries.reduce((sum, [, count]) => sum + count, 0);
  const unclassified = overallTotal - classifiedTotal;

  const counts: CategoryCount[] = entries.map(([key, count]) => ({ key, label: categoryLabel(key, locale), count }));
  if (unclassified > 0) {
    counts.push({ key: UNCLASSIFIED_KEY, label: categoryLabel(UNCLASSIFIED_KEY, locale), count: unclassified });
  }
  return counts.sort((a, b) => b.count - a.count);
}

import { categoryColorClasses, categoryLabel } from "@/lib/categories";
import type { Locale } from "@/lib/i18n";

function TagIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3 w-3 shrink-0" fill="none" aria-hidden="true">
      <path
        d="M2 2h5.6L14 8.4a1 1 0 0 1 0 1.4l-4.2 4.2a1 1 0 0 1-1.4 0L2 7.6V2Z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <circle cx="5.2" cy="5.2" r="0.9" fill="currentColor" />
    </svg>
  );
}

/** Talebin kategorisini gösteren rozet. Her kategori küçük, tekrar eden bir
 * paletten (bkz. lib/categories.ts CATEGORY_COLOR) kendi rengini alır —
 * sadece renge güvenmemek için ikon + metinle birlikte gösterilir. */
export default function CategoryBadge({ category, locale }: { category: string | null; locale: Locale }) {
  if (category === null) {
    return <span className="text-[12px] text-faint">—</span>;
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${categoryColorClasses(category)}`}
    >
      <TagIcon />
      {categoryLabel(category, locale)}
    </span>
  );
}

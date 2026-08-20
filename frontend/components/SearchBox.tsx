"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useLocale } from "@/components/LocaleProvider";

const DEBOUNCE_MS = 400;

/** URL'e `?q=` yazan, debounce'lu bir arama kutusu — sunucu tarafı
 * CategoryFilterBar/Pagination ile aynı URL-state deseni. Yeni bir arama
 * girildiğinde `page` her zaman silinir (sayfa 1'e dönülür). */
export default function SearchBox() {
  const { t } = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [value, setValue] = useState(searchParams.get("q") ?? "");

  useEffect(() => {
    const handle = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) params.set("q", value);
      else params.delete("q");
      params.delete("page");
      const qs = params.toString();
      router.push(qs ? `${pathname}?${qs}` : pathname);
    }, DEBOUNCE_MS);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <input
      type="search"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={t("dashboard.searchPlaceholder")}
      aria-label={t("dashboard.searchPlaceholder")}
      className="w-full max-w-xs rounded-lg border border-border bg-surface px-3.5 py-2 text-[13.5px] text-foreground placeholder:text-faint focus:border-accent focus:outline-none"
    />
  );
}

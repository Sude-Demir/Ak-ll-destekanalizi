import { cookies } from "next/headers";

import { DEFAULT_LOCALE, LOCALE_COOKIE, type Locale } from "@/lib/i18n";

/** Server component'lerde kullanılır — `next/headers` içerdiği için client
 * component'lere import EDİLEMEZ (bkz. lib/i18n.ts, orada yok bilerek). */
export async function getLocale(): Promise<Locale> {
  const store = await cookies();
  const value = store.get(LOCALE_COOKIE)?.value;
  return value === "en" ? "en" : DEFAULT_LOCALE;
}

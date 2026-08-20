import { cookies } from "next/headers";

import { DEFAULT_THEME, isTheme, THEME_COOKIE, type Theme } from "@/lib/theme";

/** Server component'lerde kullanılır — `next/headers` içerdiği için client
 * component'lere import EDİLEMEZ (bkz. lib/i18n-server.ts, aynı desen). */
export async function getTheme(): Promise<Theme> {
  const store = await cookies();
  const value = store.get(THEME_COOKIE)?.value;
  return isTheme(value) ? value : DEFAULT_THEME;
}

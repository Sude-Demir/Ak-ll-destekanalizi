export type Theme = "system" | "light" | "dark";

export const THEME_COOKIE = "theme";
export const DEFAULT_THEME: Theme = "system";

export function isTheme(value: string | undefined | null): value is Theme {
  return value === "system" || value === "light" || value === "dark";
}

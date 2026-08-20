import { Show, UserButton } from "@clerk/nextjs";
import Link from "next/link";

import LanguageSwitcher from "@/components/LanguageSwitcher";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function AppBar() {
  const locale = await getLocale();

  // bkz. https://clerk.com/changelog/2026-03-03-core-3 — <SignedIn>/<SignedOut>
  // Core 3'te kaldırıldı, yerini <Show when="signed-in|signed-out"> aldı.
  const signedOutFallback = (
    <Link href="/sign-in" className="text-[13px] font-semibold text-muted hover:text-foreground">
      {t(locale, "common.signIn")}
    </Link>
  );

  return (
    <header className="sticky top-0 z-10 h-14 border-b border-border bg-surface">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between gap-2.5 px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-xs font-extrabold text-white">
            AD
          </span>
          <span className="text-[15px] font-bold tracking-tight text-foreground">
            Akıllı Destek
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <ThemeSwitcher />
          <LanguageSwitcher />
          <Show when="signed-in" fallback={signedOutFallback}>
            <UserButton />
          </Show>
        </div>
      </div>
    </header>
  );
}

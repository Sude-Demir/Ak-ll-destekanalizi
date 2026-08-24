import Link from "next/link";

import { formatPercent, t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

// Hero ve kapanış CTA'sı bilinçli olarak sabit koyu bir gradyan kullanıyor
// (site temasından bağımsız — bkz. AnalyticsHero'daki "marka bandı" deseni),
// bu yüzden içlerindeki metin/renkler de tema değişkenleri yerine bu koyu
// zemine göre elle seçildi.
const DARK_GRADIENT = "linear-gradient(160deg, #0b0b10 0%, #14121f 55%, #0d0d14 100%)";

function TicketIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 8.5 12 3l9 5.5V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z" strokeLinejoin="round" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="12" cy="12" r="4" />
      <path
        d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CheckShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 3 4 6.5V12c0 5 3.4 8 8 9 4.6-1 8-4 8-9V6.5Z" strokeLinejoin="round" />
      <path d="m8.5 12.2 2.4 2.3 4.6-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path
        d="M12 9v4M12 16.5h.01M10.3 4.3 2.9 17a1.8 1.8 0 0 0 1.6 2.7h15a1.8 1.8 0 0 0 1.6-2.7L13.7 4.3a1.8 1.8 0 0 0-3.4 0Z"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.6" className="shrink-0 text-faint">
      <path d="M4 12h16M14 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function JourneyStep({ icon, label, index }: { icon: React.ReactNode; label: string; index: number }) {
  return (
    <div className="flex flex-1 items-center gap-4 rounded-2xl border border-border bg-surface px-5 py-4 shadow-[0_1px_2px_rgba(20,20,19,0.04)]">
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-tech/10 text-accent-tech">
        {icon}
      </span>
      <div className="flex flex-col">
        <span className="font-mono text-[10.5px] font-semibold tracking-widest text-faint">0{index}</span>
        <span className="text-[14px] font-semibold text-foreground">{label}</span>
      </div>
    </div>
  );
}

export default async function LandingPage() {
  const locale = await getLocale();

  return (
    <main className="flex-1">
      {/* Hero — koyu, camsı (glassmorphism) zemin */}
      <section className="relative overflow-hidden" style={{ background: DARK_GRADIENT }}>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-32 -top-32 h-[420px] w-[420px] rounded-full opacity-30 blur-[110px]"
          style={{ background: "var(--accent-tech)" }}
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 top-32 h-[320px] w-[320px] rounded-full opacity-20 blur-[100px]"
          style={{ background: "#7a3b5e" }}
        />

        <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 md:grid-cols-[0.9fr_1.1fr] md:gap-16 md:px-10 md:py-28">
          <div className="flex flex-col gap-6">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 text-[11.5px] font-semibold tracking-wide text-white/70 backdrop-blur-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-accent-tech" />
              {t(locale, "landing.eyebrow")}
            </span>
            <h1 className="text-balance text-[36px] font-bold leading-[1.14] tracking-tight text-white md:text-[46px]">
              {t(locale, "landing.headline")}
            </h1>
            <p className="max-w-[48ch] text-[16px] leading-relaxed text-white/60">{t(locale, "landing.subheadline")}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <Link
                href="/sign-in"
                className="rounded-xl bg-accent-tech px-6 py-3 text-[14px] font-semibold text-white shadow-[0_0_0_1px_rgba(255,255,255,0.08),0_8px_30px_-8px_var(--accent-tech)] transition hover:brightness-110"
              >
                {t(locale, "common.signIn")}
              </Link>
              <a
                href="#nasil-calisir"
                className="rounded-xl border border-white/15 px-5 py-3 text-[14px] font-semibold text-white/85 backdrop-blur-sm transition hover:border-white/30 hover:bg-white/[0.04]"
              >
                {t(locale, "landing.ctaSecondary")}
              </a>
            </div>
          </div>

          {/* Product mockup card — DraftPanel'in cam efektli bir örneği */}
          <div
            className="relative overflow-hidden rounded-2xl border border-white/10 backdrop-blur-xl"
            style={{
              background: "linear-gradient(160deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02))",
              boxShadow: "0 30px 80px -30px rgba(0,0,0,0.7), 0 0 60px -20px rgba(108,99,255,0.3)",
            }}
          >
            <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-white/[0.03] px-5 py-3.5">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-tech/30 bg-accent-tech/15 px-2.5 py-1 text-[11.5px] font-semibold text-accent-tech">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-tech" />
                {t(locale, "draftPanel.statusPending")}
              </span>
              <span className="text-[12px] font-semibold tabular-nums text-white/50">
                {t(locale, "draftPanel.confidence")}: {formatPercent(0.82, locale)}
              </span>
            </div>
            <div className="px-5 py-5">
              <p className="text-[14px] leading-relaxed text-white/85">{t(locale, "landing.mockupDraftText")}</p>
              <div className="mt-4 border-t border-dashed border-white/10 pt-3.5">
                <p className="text-[10.5px] font-bold tracking-wide text-white/40 uppercase">
                  {t(locale, "draftPanel.sourcesHeading")}
                </p>
                <div className="mt-2 flex items-baseline gap-2.5 text-[12.5px]">
                  <span className="shrink-0 rounded-md border border-white/10 bg-white/[0.05] px-2 py-0.5 text-[11px] font-semibold text-white/70">
                    {t(locale, "landing.mockupSourceCategory")}
                  </span>
                  <span className="text-white/55">{t(locale, "landing.mockupSourceQuestion")}</span>
                </div>
              </div>
              <div aria-hidden="true" className="mt-4 flex items-center gap-2 border-t border-white/10 pt-4">
                <span className="rounded-lg bg-accent-tech px-3.5 py-1.5 text-[13px] font-semibold text-white">
                  {t(locale, "draftPanel.approve")}
                </span>
                <span className="rounded-lg border border-white/15 px-3.5 py-1.5 text-[13px] font-semibold text-white/80">
                  {t(locale, "draftPanel.edit")}
                </span>
                <span className="px-3.5 py-1.5 text-[13px] font-semibold text-white/40">{t(locale, "draftPanel.reject")}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Journey strip — açık, kart tabanlı adım göstergesi */}
      <section id="nasil-calisir" className="border-b border-border bg-background px-6 py-16 md:px-10">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 md:flex-row md:items-stretch">
          <JourneyStep icon={<TicketIcon />} label={t(locale, "landing.journeyStep1")} index={1} />
          <div className="hidden items-center justify-center px-1 md:flex">
            <ArrowIcon />
          </div>
          <JourneyStep icon={<SparkleIcon />} label={t(locale, "landing.journeyStep2")} index={2} />
          <div className="hidden items-center justify-center px-1 md:flex">
            <ArrowIcon />
          </div>
          <JourneyStep icon={<CheckShieldIcon />} label={t(locale, "landing.journeyStep3")} index={3} />
        </div>
      </section>

      {/* Why AI + human — yükseltilmiş kartlar */}
      <section className="mx-auto max-w-5xl px-6 py-20 md:px-10">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <div className="rounded-2xl border border-border bg-surface p-7 shadow-[0_1px_2px_rgba(20,20,19,0.04)] transition hover:shadow-[0_16px_36px_-16px_rgba(20,20,19,0.14)]">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              <WarningIcon />
            </div>
            <h3 className="mt-4 text-[16.5px] font-semibold text-foreground">{t(locale, "landing.whyAiTitle")}</h3>
            <p className="mt-2 text-[14px] leading-relaxed text-muted">{t(locale, "landing.whyAiBody")}</p>
          </div>
          <div className="rounded-2xl border border-border bg-surface p-7 shadow-[0_1px_2px_rgba(20,20,19,0.04)] transition hover:shadow-[0_16px_36px_-16px_rgba(20,20,19,0.14)]">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-tech/10 text-accent-tech">
              <CheckShieldIcon />
            </div>
            <h3 className="mt-4 text-[16.5px] font-semibold text-foreground">{t(locale, "landing.whyHumanTitle")}</h3>
            <p className="mt-2 text-[14px] leading-relaxed text-muted">{t(locale, "landing.whyHumanBody")}</p>
          </div>
        </div>
      </section>

      {/* Closing CTA — hero ile aynı koyu/camsı dilin devamı */}
      <section className="relative overflow-hidden px-6 py-16 md:px-10" style={{ background: DARK_GRADIENT }}>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute right-[-8%] top-1/2 h-[280px] w-[280px] -translate-y-1/2 rounded-full opacity-25 blur-[100px]"
          style={{ background: "var(--accent-tech)" }}
        />
        <div className="relative mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-6">
          <h2 className="max-w-[44ch] text-balance text-[22px] font-bold text-white">{t(locale, "landing.closingHeading")}</h2>
          <Link
            href="/sign-in"
            className="shrink-0 rounded-xl bg-accent-tech px-6 py-3 text-[14px] font-semibold text-white shadow-[0_8px_30px_-8px_var(--accent-tech)] transition hover:brightness-110"
          >
            {t(locale, "common.signIn")}
          </Link>
        </div>
      </section>
    </main>
  );
}

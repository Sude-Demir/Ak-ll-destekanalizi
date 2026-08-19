"use client";

import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";

export default function CopyInviteLink({ link }: { link: string }) {
  const { t } = useLocale();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="mt-2 flex items-center gap-2">
      <code className="min-w-0 flex-1 truncate rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-[12px] text-muted">
        {link}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-lg border border-border px-2.5 py-1.5 text-[12px] font-semibold text-foreground hover:border-border-strong"
      >
        {copied ? t("copyLink.copied") : t("copyLink.copy")}
      </button>
    </div>
  );
}

"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { createAgentInvite } from "@/lib/api";

export default function CreateInviteForm() {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const router = useRouter();

  const emailId = useId();
  const nameId = useId();

  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      await createAgentInvite({ email, name: name.trim() || undefined }, token);
      setEmail("");
      setName("");
      router.refresh();
    } catch {
      setError(t("inviteForm.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-surface p-5 shadow-sm">
      <div className="min-w-[220px] flex-1">
        <label htmlFor={emailId} className="text-[13px] font-semibold text-foreground">
          {t("inviteForm.email")}
        </label>
        <input
          id={emailId}
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ornek@sirket.com"
          className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-2.5 text-[14px] text-foreground focus:border-accent focus:outline-none"
        />
      </div>

      <div className="min-w-[180px] flex-1">
        <label htmlFor={nameId} className="text-[13px] font-semibold text-foreground">
          {t("inviteForm.name")} <span className="font-normal text-faint">{t("inviteForm.optional")}</span>
        </label>
        <input
          id={nameId}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-2.5 text-[14px] text-foreground focus:border-accent focus:outline-none"
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-accent px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? t("inviteForm.creating") : t("inviteForm.create")}
      </button>

      {error && <p className="w-full text-[13px] text-red-600">{error}</p>}
    </form>
  );
}

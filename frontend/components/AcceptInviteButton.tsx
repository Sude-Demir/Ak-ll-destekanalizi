"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { acceptAgentInvite } from "@/lib/api";

export default function AcceptInviteButton({ token }: { token: string }) {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const router = useRouter();

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAccept() {
    setSubmitting(true);
    setError(null);
    try {
      const authToken = await getToken();
      await acceptAgentInvite(token, authToken);
      router.push("/");
    } catch (err) {
      // Not: err.message backend'in kendi hata mesajını (henüz Türkçe,
      // kapsam dışı — bkz. plan) taşıyabilir; sadece genel fallback çevrilir.
      setError(err instanceof Error ? err.message : t("acceptInvite.genericError"));
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleAccept}
        disabled={submitting}
        className="rounded-lg bg-accent px-5 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? t("acceptInvite.accepting") : t("acceptInvite.accept")}
      </button>

      {error && <p className="mt-3 text-[13px] text-red-600">{error}</p>}
    </div>
  );
}

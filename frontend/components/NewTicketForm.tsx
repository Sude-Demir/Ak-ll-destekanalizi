"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { submitMyTicket } from "@/lib/api";

export default function NewTicketForm() {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const router = useRouter();

  const subjectId = useId();
  const bodyId = useId();

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      await submitMyTicket({ subject, body }, token);
      setSubject("");
      setBody("");
      router.refresh();
    } catch {
      setError(t("newTicket.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-surface p-6 shadow-sm">
      <div>
        <label htmlFor={subjectId} className="text-[13px] font-semibold text-foreground">
          {t("newTicket.subject")}
        </label>
        <input
          id={subjectId}
          type="text"
          required
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-3 text-[14px] text-foreground focus:border-accent focus:outline-none"
        />
      </div>

      <div>
        <label htmlFor={bodyId} className="text-[13px] font-semibold text-foreground">
          {t("newTicket.body")}
        </label>
        <textarea
          id={bodyId}
          required
          rows={5}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-3 text-[14px] text-foreground focus:border-accent focus:outline-none"
        />
      </div>

      {error && <p className="text-[13px] text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-accent px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? t("newTicket.submitting") : t("newTicket.submit")}
      </button>
    </form>
  );
}

"use client";

import { useId, useState } from "react";

import { submitPublicTicket } from "@/lib/api";

export default function SupportPage() {
  const nameId = useId();
  const emailId = useId();
  const subjectId = useId();
  const bodyId = useId();

  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedTicketId, setSubmittedTicketId] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const ticket = await submitPublicTicket({ customer_name: customerName, customer_email: customerEmail, subject, body });
      setSubmittedTicketId(ticket.id);
    } catch {
      setError("Talebiniz gönderilemedi. Lütfen birkaç dakika sonra tekrar deneyin.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submittedTicketId !== null) {
    return (
      <main className="mx-auto max-w-xl px-6 py-16">
        <div className="rounded-xl border border-border bg-surface p-8 text-center shadow-sm">
          <h1 className="text-[19px] font-bold tracking-tight text-foreground">Talebiniz alındı</h1>
          <p className="mt-2 text-[14px] text-muted">
            Talep numaranız <span className="font-semibold text-foreground">#{submittedTicketId}</span>. Ekibimiz en
            kısa sürede size dönüş yapacak.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <h1 className="text-[22px] font-bold tracking-tight text-foreground">Bize Ulaşın</h1>
      <p className="mt-1 text-[13.5px] text-muted">
        Bir sorunuz veya sorununuz mu var? Aşağıdaki formu doldurun, destek ekibimiz size dönüş yapsın.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div>
          <label htmlFor={nameId} className="text-[13px] font-semibold text-foreground">
            Ad Soyad
          </label>
          <input
            id={nameId}
            type="text"
            required
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-3 text-[14px] text-foreground focus:border-accent focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor={emailId} className="text-[13px] font-semibold text-foreground">
            E-posta
          </label>
          <input
            id={emailId}
            type="email"
            required
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
            className="mt-1.5 w-full rounded-lg border border-border bg-surface-2 p-3 text-[14px] text-foreground focus:border-accent focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor={subjectId} className="text-[13px] font-semibold text-foreground">
            Konu
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
            Mesajınız
          </label>
          <textarea
            id={bodyId}
            required
            rows={6}
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
          {submitting ? "Gönderiliyor…" : "Talebi Gönder"}
        </button>
      </form>
    </main>
  );
}

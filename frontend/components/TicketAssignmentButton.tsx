"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { updateTicketAssignment } from "@/lib/api";

// Bir talebi "üstlenme" — birden fazla temsilci aynı talep üzerinde
// çakışarak çalışmasın diye (bkz. CLAUDE.md "özgün 10 özellik" listesi #5).
// Kimin "ben" olduğunu Clerk'in oturum bilgisinden (kullanıcının tam adı)
// çözüp assigned_agent_name ile karşılaştırıyoruz — ekstra bir API çağrısı
// gerekmeden "sen üstlendin" ile "X üstlendi" ayrımını yapabiliyoruz.
export default function TicketAssignmentButton({
  ticketId,
  initialAssignedAgentName,
}: {
  ticketId: number;
  initialAssignedAgentName: string | null;
}) {
  const { getToken } = useAuth();
  const { user } = useUser();
  const { t } = useLocale();
  const [assignedAgentName, setAssignedAgentName] = useState(initialAssignedAgentName);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isMine = assignedAgentName !== null && assignedAgentName === user?.fullName;

  async function handleClick(claim: boolean) {
    setSubmitting(true);
    setError(null);
    try {
      const token = await getToken();
      const updated = await updateTicketAssignment(ticketId, claim, token);
      setAssignedAgentName(updated.assigned_agent_name);
    } catch {
      setError(t("ticketDetail.assignmentError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex items-center gap-2.5">
      <span className="text-[12.5px] text-muted">
        {assignedAgentName === null
          ? t("ticketDetail.unassigned")
          : isMine
            ? t("ticketDetail.assignedToYou")
            : t("ticketDetail.assignedTo", { name: assignedAgentName })}
      </span>
      {assignedAgentName === null && (
        <button
          onClick={() => handleClick(true)}
          disabled={submitting}
          className="rounded-lg border border-border px-2.5 py-1 text-[12.5px] font-semibold text-foreground hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("ticketDetail.claim")}
        </button>
      )}
      {assignedAgentName !== null && !isMine && (
        <button
          onClick={() => handleClick(true)}
          disabled={submitting}
          className="rounded-lg border border-border px-2.5 py-1 text-[12.5px] font-semibold text-foreground hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("ticketDetail.takeOver")}
        </button>
      )}
      {assignedAgentName !== null && (
        <button
          onClick={() => handleClick(false)}
          disabled={submitting}
          className="rounded-lg px-2.5 py-1 text-[12.5px] font-semibold text-muted hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("ticketDetail.release")}
        </button>
      )}
      {error && <span className="text-[12px] text-red-600">{error}</span>}
    </div>
  );
}

"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import StatusPill from "@/components/StatusPill";
import {
  generateKbSuggestion,
  updateKbSuggestionStatus,
  type KbSuggestion,
  type KbSuggestionDecision,
} from "@/lib/api";
import { DRAFT_STATUS_PILL_CLASSES } from "@/lib/draftStatus";
import type { TranslationKey } from "@/lib/i18n";

const STATUS_LABEL_KEYS: Record<string, TranslationKey> = {
  pending: "kbSuggestion.statusPending",
  approved: "kbSuggestion.statusApproved",
  rejected: "kbSuggestion.statusRejected",
};

function SuggestionCard({
  suggestion,
  ticketId,
  onUpdated,
}: {
  suggestion: KbSuggestion;
  ticketId: number;
  onUpdated: (updated: KbSuggestion) => void;
}) {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const [isEditing, setIsEditing] = useState(false);
  const [question, setQuestion] = useState(suggestion.question);
  const [answer, setAnswer] = useState(suggestion.answer);
  const [submitting, setSubmitting] = useState<KbSuggestionDecision | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = suggestion.status === "pending";

  async function handleDecision(decision: KbSuggestionDecision) {
    setSubmitting(decision);
    setError(null);
    try {
      const token = await getToken();
      const edits = decision === "approved" ? { question, answer } : undefined;
      const updated = await updateKbSuggestionStatus(ticketId, suggestion.id, decision, token, edits);
      onUpdated(updated);
      setIsEditing(false);
    } catch {
      setError(t("kbSuggestion.saveError"));
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border border-l-[3px] border-l-accent-tech bg-surface shadow-sm">
      <div className="flex items-center justify-between gap-3 bg-accent-tech/10 px-5 py-3">
        <StatusPill
          label={STATUS_LABEL_KEYS[suggestion.status] ? t(STATUS_LABEL_KEYS[suggestion.status]) : suggestion.status}
          className={DRAFT_STATUS_PILL_CLASSES[suggestion.status] ?? "bg-surface-2 text-muted"}
        />
      </div>

      <div className="px-5 py-4">
        <p className="text-[10.5px] font-bold tracking-wide text-faint uppercase">
          {t("kbSuggestion.questionLabel")}
        </p>
        {isEditing ? (
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="mt-1 w-full rounded-lg border border-border bg-surface-2 p-2 text-[14px] text-foreground focus:border-accent-tech focus:outline-none"
          />
        ) : (
          <p className="mt-1 text-[14px] font-semibold text-foreground">{suggestion.question}</p>
        )}

        <p className="mt-3 text-[10.5px] font-bold tracking-wide text-faint uppercase">
          {t("kbSuggestion.answerLabel")}
        </p>
        {isEditing ? (
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-border bg-surface-2 p-2 text-[14px] text-foreground focus:border-accent-tech focus:outline-none"
          />
        ) : (
          <p className="mt-1 whitespace-pre-wrap text-[14px] text-muted">{suggestion.answer}</p>
        )}

        {error && <p className="mt-3 text-[13px] text-red-600">{error}</p>}

        {isPending && (
          <div className="mt-4 flex items-center gap-2 border-t border-border pt-4">
            {isEditing ? (
              <>
                <button
                  onClick={() => handleDecision("approved")}
                  disabled={submitting !== null || !question.trim() || !answer.trim()}
                  className="rounded-lg bg-accent-tech px-3.5 py-1.5 text-[13px] font-semibold text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "approved" ? t("kbSuggestion.saving") : t("kbSuggestion.save")}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setQuestion(suggestion.question);
                    setAnswer(suggestion.answer);
                  }}
                  disabled={submitting !== null}
                  className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] font-semibold text-muted hover:bg-surface-2"
                >
                  {t("kbSuggestion.cancel")}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleDecision("approved")}
                  disabled={submitting !== null}
                  className="rounded-lg bg-accent-tech px-3.5 py-1.5 text-[13px] font-semibold text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "approved" ? t("kbSuggestion.approving") : t("kbSuggestion.approve")}
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  disabled={submitting !== null}
                  className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] font-semibold text-foreground hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {t("kbSuggestion.edit")}
                </button>
                <button
                  onClick={() => handleDecision("rejected")}
                  disabled={submitting !== null}
                  className="rounded-lg px-3.5 py-1.5 text-[13px] font-semibold text-muted hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting === "rejected" ? t("kbSuggestion.rejecting") : t("kbSuggestion.reject")}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Çözülmüş bir talebin yanıtından, gelecekteki benzer talepler için otomatik
// SSS maddesi önerisi — sadece talebin onaylı/düzenlenmiş bir yanıtı varken
// (backend de aynı kısıtı uyguluyor, bkz. app/routers/kb_suggestions.py).
export default function KbSuggestionPanel({
  ticketId,
  isAnswered,
  initialSuggestions,
}: {
  ticketId: number;
  isAnswered: boolean;
  initialSuggestions: KbSuggestion[];
}) {
  const { getToken } = useAuth();
  const { t } = useLocale();
  const [suggestions, setSuggestions] = useState(initialSuggestions);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isAnswered && suggestions.length === 0) return null;

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const suggestion = await generateKbSuggestion(ticketId, token);
      setSuggestions((prev) => [suggestion, ...prev]);
    } catch {
      setError(t("kbSuggestion.generateError"));
    } finally {
      setLoading(false);
    }
  }

  function handleSuggestionUpdated(updated: KbSuggestion) {
    setSuggestions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  }

  return (
    <div className="mt-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-[16px] font-bold tracking-tight text-foreground">{t("kbSuggestion.heading")}</h2>
          <p className="mt-0.5 text-[12.5px] text-muted">{t("kbSuggestion.subtitle")}</p>
        </div>
        {isAnswered && (
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="shrink-0 rounded-lg bg-accent-tech px-4 py-2 text-[13.5px] font-semibold text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? t("kbSuggestion.generating") : t("kbSuggestion.generate")}
          </button>
        )}
      </div>

      {error && <p className="mt-3 text-[13.5px] text-red-600">{error}</p>}

      {suggestions.length > 0 && (
        <div className="mt-4 space-y-4">
          {suggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              ticketId={ticketId}
              onUpdated={handleSuggestionUpdated}
            />
          ))}
        </div>
      )}
    </div>
  );
}

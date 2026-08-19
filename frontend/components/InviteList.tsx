import CopyInviteLink from "@/components/CopyInviteLink";
import StatusPill from "@/components/StatusPill";
import type { AgentInvite } from "@/lib/api";
import { formatDate, t, type TranslationKey } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

const STATUS_LABEL_KEYS: Record<AgentInvite["status"], TranslationKey> = {
  pending: "inviteList.pending",
  accepted: "inviteList.accepted",
  expired: "inviteList.expired",
};

const STATUS_STYLES: Record<AgentInvite["status"], string> = {
  pending: "bg-status-wait-bg text-status-wait-fg",
  accepted: "bg-status-done-bg text-status-done-fg",
  expired: "bg-surface-2 text-muted",
};

export default async function InviteList({ invites }: { invites: AgentInvite[] }) {
  const locale = await getLocale();

  if (invites.length === 0) {
    return <p className="mt-6 text-muted">{t(locale, "inviteList.empty")}</p>;
  }

  return (
    <div className="mt-6 space-y-3">
      {invites.map((invite) => (
        <div key={invite.id} className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-[13.8px] font-semibold text-foreground">
                {invite.name ? `${invite.name} · ` : ""}
                {invite.email}
              </div>
              <div className="text-[12px] text-muted">
                {invite.status === "pending"
                  ? t(locale, "inviteList.validUntil", { date: formatDate(invite.expires_at, locale) })
                  : t(locale, "inviteList.createdAt", { date: formatDate(invite.created_at, locale) })}
              </div>
            </div>
            <StatusPill
              label={t(locale, STATUS_LABEL_KEYS[invite.status])}
              className={STATUS_STYLES[invite.status]}
            />
          </div>

          {invite.status === "pending" && <CopyInviteLink link={`${APP_URL}/invite/${invite.token}`} />}
        </div>
      ))}
    </div>
  );
}

import { notFound } from "next/navigation";

import AcceptInviteButton from "@/components/AcceptInviteButton";
import { fetchInvitePreview } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function InvitePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const locale = await getLocale();
  const { token } = await params;

  let invite;
  try {
    invite = await fetchInvitePreview(token);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto flex max-w-md flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <h1 className="text-[22px] font-bold tracking-tight text-foreground">{t(locale, "inviteAccept.heading")}</h1>

      {invite.status === "pending" && (
        <>
          <p className="mt-2 text-[14px] text-muted">
            {t(locale, "inviteAccept.pendingPrefix")}{" "}
            <span className="font-semibold text-foreground">{invite.email}</span>
            {t(locale, "inviteAccept.pendingSuffix")}
          </p>
          <div className="mt-6">
            <AcceptInviteButton token={token} />
          </div>
        </>
      )}

      {invite.status === "accepted" && <p className="mt-2 text-[14px] text-muted">{t(locale, "inviteAccept.accepted")}</p>}

      {invite.status === "expired" && (
        <p className="mt-2 text-[14px] text-muted">{t(locale, "inviteAccept.expired")}</p>
      )}
    </main>
  );
}

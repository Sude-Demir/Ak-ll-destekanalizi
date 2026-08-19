import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

import CreateInviteForm from "@/components/CreateInviteForm";
import InviteList from "@/components/InviteList";
import { fetchAgentInvites } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function TeamPage() {
  const locale = await getLocale();
  const { getToken } = await auth();
  const token = await getToken();

  let invites;
  let errorMessage: string | null = null;

  try {
    invites = await fetchAgentInvites(token);
  } catch (error) {
    // Bir müşteri hesabı buraya elle gelirse backend 403 döner (bkz.
    // backend/app/routers/agent_invites.py require_agent).
    if (error instanceof Error && error.message.includes("403")) {
      redirect("/portal");
    }
    errorMessage = t(locale, "team.loadError");
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-[22px] font-bold tracking-tight text-foreground">{t(locale, "team.title")}</h1>
      <p className="mt-1 text-[13.5px] text-muted">{t(locale, "team.subtitle")}</p>

      <div className="mt-6">
        <CreateInviteForm />
      </div>

      {errorMessage ? <p className="mt-6 text-red-600">{errorMessage}</p> : <InviteList invites={invites ?? []} />}
    </main>
  );
}

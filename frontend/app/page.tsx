import { auth } from "@clerk/nextjs/server";
import Link from "next/link";

import { fetchMe } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function Home() {
  const locale = await getLocale();
  const { userId, getToken } = await auth();

  // Oturum var diye otomatik olarak panele/portala atlamıyoruz — tarayıcıda
  // eski bir oturum kalmış olsa bile önce burada bilinçli bir tıklama
  // isteniyor (kullanıcı isteği: "hangi hesapta kaldığına direkt girmesin").
  if (!userId) {
    return (
      <main className="mx-auto flex max-w-xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        {/* Ürün adı bir marka ismi — dile göre çevrilmiyor, sabit kalıyor. */}
        <h1 className="text-[26px] font-bold tracking-tight text-foreground">Akıllı Destek Asistanı</h1>
        <p className="mt-2 text-[14px] text-muted">{t(locale, "welcome.subtitleSignedOut")}</p>
        <Link
          href="/sign-in"
          className="mt-6 rounded-lg bg-accent px-5 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong"
        >
          {t(locale, "common.signIn")}
        </Link>
      </main>
    );
  }

  const token = await getToken();
  const me = await fetchMe(token);
  const firstName = me.name.split(" ")[0];

  return (
    <main className="mx-auto flex max-w-xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <h1 className="text-[26px] font-bold tracking-tight text-foreground">
        {t(locale, "welcome.greeting", { name: firstName })}
      </h1>
      <p className="mt-2 text-[14px] text-muted">
        {t(locale, me.is_agent ? "welcome.subtitleAgent" : "welcome.subtitleCustomer")}
      </p>
      <Link
        href={me.is_agent ? "/dashboard" : "/portal"}
        className="mt-6 rounded-lg bg-accent px-5 py-2.5 text-[14px] font-semibold text-white hover:bg-accent-strong"
      >
        {t(locale, me.is_agent ? "welcome.goToDashboard" : "welcome.goToPortal")}
      </Link>
    </main>
  );
}

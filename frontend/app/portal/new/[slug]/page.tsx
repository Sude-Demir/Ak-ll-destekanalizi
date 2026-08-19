import Link from "next/link";
import { notFound } from "next/navigation";

import NewTicketForm from "@/components/NewTicketForm";
import { fetchCompany } from "@/lib/api";
import { t } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";

export default async function NewCompanyTicketPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const locale = await getLocale();
  const { slug } = await params;

  let company;
  try {
    company = await fetchCompany(slug);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <Link href="/portal" className="text-[13px] font-semibold text-accent hover:underline">
        {t(locale, "newTicket.back")}
      </Link>

      <h1 className="mt-3 text-[22px] font-bold tracking-tight text-foreground">
        {t(locale, "newTicket.heading", { company: company.name })}
      </h1>

      <div className="mt-6">
        <NewTicketForm companySlug={slug} />
      </div>
    </main>
  );
}

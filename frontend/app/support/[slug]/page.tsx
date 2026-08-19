import { notFound } from "next/navigation";

import SupportForm from "@/components/SupportForm";
import { fetchCompany } from "@/lib/api";

export default async function SupportPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let company;
  try {
    company = await fetchCompany(slug);
  } catch {
    notFound();
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <SupportForm slug={slug} companyName={company.name} />
    </main>
  );
}

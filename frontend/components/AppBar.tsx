import Link from "next/link";

export default function AppBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-surface">
      <div className="mx-auto flex max-w-6xl items-center gap-2.5 px-6 py-3.5">
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-xs font-extrabold text-white">
            AD
          </span>
          <span className="text-[15px] font-bold tracking-tight text-foreground">
            Akıllı Destek
          </span>
        </Link>
      </div>
    </header>
  );
}

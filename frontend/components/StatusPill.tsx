export default function StatusPill({ label, className }: { label: string; className: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11.5px] font-semibold before:h-1.5 before:w-1.5 before:rounded-full before:bg-current ${className}`}
    >
      {label}
    </span>
  );
}

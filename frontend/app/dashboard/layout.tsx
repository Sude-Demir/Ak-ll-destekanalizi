import DashboardSidebar from "@/components/DashboardSidebar";

// Next.js nested layout — /dashboard, /dashboard/analytics, /dashboard/team,
// /dashboard/tickets/[id] hepsini sarar. /portal ve /support ayrı route
// ağaçları oldukları için bundan etkilenmez.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col md:flex-row md:items-start">
      <DashboardSidebar />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

import DashboardSidebar from "@/components/DashboardSidebar";
import NotificationBell from "@/components/NotificationBell";

// Next.js nested layout — /dashboard, /dashboard/analytics, /dashboard/team,
// /dashboard/tickets/[id] hepsini sarar. /portal ve /support ayrı route
// ağaçları oldukları için bundan etkilenmez. Bu alt ağacın tamamı zaten
// temsilciye özel olduğu için (require_agent ile korunan uç noktalar), bell
// burada ekstra bir rol kontrolü yapmadan gösterilebilir.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col md:flex-row md:items-start">
      <DashboardSidebar />
      <div className="min-w-0 flex-1">
        <div className="flex justify-end px-4 pt-3 md:px-6">
          <NotificationBell />
        </div>
        {children}
      </div>
    </div>
  );
}

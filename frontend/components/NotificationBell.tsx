"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useLocale } from "@/components/LocaleProvider";
import { fetchNotifications, markAllNotificationsRead, type Notification } from "@/lib/api";
import { formatDate } from "@/lib/i18n";

// Yeni lead/acil talep tespit edildiğinde temsilciye görünen bildirim zili
// (bkz. CLAUDE.md "özgün 10 özellik" listesi #10). Gerçek zamanlı yerine
// düzenli aralıklarla yoklama (polling) yapıyor — WebSocket/SSE gibi ek bir
// altyapı gerektirmeden "yeterince gerçek zamanlı" bir MVP için (bkz.
// CLAUDE.md "ince soyutlama, ağır framework değil").
const POLL_INTERVAL_MS = 20_000;

export default function NotificationBell() {
  const { getToken } = useAuth();
  const { locale, t } = useLocale();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const token = await getToken();
        const items = await fetchNotifications(token);
        if (!cancelled) setNotifications(items);
      } catch {
        // Sessizce yut — bu bir yan gösterge paneli, ana akışı bozmamalı.
      }
    }

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [getToken]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => n.read_at === null).length;

  async function handleToggle() {
    const opening = !open;
    setOpen(opening);
    if (opening && unreadCount > 0) {
      try {
        const token = await getToken();
        const updated = await markAllNotificationsRead(token);
        setNotifications(updated);
      } catch {
        // Sessizce yut — okunmamış rozeti bir sonraki yoklamada düzelir.
      }
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={handleToggle}
        aria-label={t("notifications.bellAriaLabel")}
        className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted hover:bg-surface-2 hover:text-foreground"
      >
        <BellIcon />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border bg-surface p-2 shadow-lg">
          <div className="px-2 py-1.5 text-[12.5px] font-bold text-foreground">{t("notifications.heading")}</div>
          {notifications.length === 0 ? (
            <p className="px-2 py-3 text-[12.5px] text-muted">{t("notifications.empty")}</p>
          ) : (
            <ul className="max-h-80 space-y-0.5 overflow-y-auto">
              {notifications.map((notification) => (
                <li key={notification.id}>
                  <Link
                    href={`/dashboard/tickets/${notification.ticket_id}`}
                    onClick={() => setOpen(false)}
                    className={`block rounded-lg px-2 py-2 text-[12.5px] hover:bg-surface-2 ${
                      notification.read_at === null ? "bg-accent-soft" : ""
                    }`}
                  >
                    <span className="font-semibold text-foreground">
                      {t(
                        notification.type === "urgent" ? "notifications.urgentMessage" : "notifications.leadMessage",
                        { subject: notification.ticket_subject }
                      )}
                    </span>
                    <span className="mt-0.5 block text-[11px] text-faint">
                      {formatDate(notification.created_at, locale)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-[18px] w-[18px]">
      <path
        d="M6 8a6 6 0 1 1 12 0c0 3.5 1 5.5 1.5 6.5h-15C5 13.5 6 11.5 6 8Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M9.5 17a2.5 2.5 0 0 0 5 0" strokeLinecap="round" />
    </svg>
  );
}

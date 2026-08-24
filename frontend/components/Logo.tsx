// supportIQ marka simgesi: bir destek diyalog balonu (kulaklık yerine daha
// küçük boyutlarda okunaklı olduğu için balon tercih edildi) ile içine
// gömülü, düğüm noktalarıyla işaretlenmiş yükselen bir sinyal/analitik
// çizgisinin birleşimi. Balon = destek, çizgi+düğümler = analitik/yapay
// zekâ. Renkler CSS değişkenlerinden geliyor (var(--foreground)/var(--accent-tech))
// ki tema (açık/koyu) değiştiğinde ikon otomatik uyum sağlasın.
export function LogoMark({ size = 28, className = "" }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} className={className} aria-hidden="true">
      <rect x="3.5" y="5" width="25" height="16.5" rx="7.5" fill="var(--foreground)" />
      <path d="M9.5 21.3 L9.5 27 L15 21.3 Z" fill="var(--foreground)" />
      <polyline
        points="9,16.5 13.5,11.3 17.5,14.3 21.5,9.3"
        fill="none"
        stroke="var(--accent-tech)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="16.5" r="1.4" fill="var(--accent-tech)" />
      <circle cx="13.5" cy="11.3" r="1.4" fill="var(--accent-tech)" />
      <circle cx="17.5" cy="14.3" r="1.4" fill="var(--accent-tech)" />
      <circle cx="21.5" cy="9.3" r="1.8" fill="var(--surface)" stroke="var(--accent-tech)" strokeWidth="1.5" />
    </svg>
  );
}

// "support" nötr (foreground), "IQ" teknoloji/AI hissi veren vurgulu renkte
// (accent-tech) — kullanıcı isteğiyle birebir aynı ayrım.
export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`font-bold tracking-tight ${className}`}>
      <span className="text-foreground">support</span>
      <span className="text-accent-tech">IQ</span>
    </span>
  );
}

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`flex items-center gap-2 ${className}`}>
      <LogoMark size={28} />
      <Wordmark className="text-[15px]" />
    </span>
  );
}

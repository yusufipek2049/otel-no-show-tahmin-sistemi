import Link from "next/link";

type AppShellProps = {
  children: React.ReactNode;
  currentRoute: "/dashboard" | "/reservations" | "/reports";
};

const navigation = [
  { href: "/dashboard", label: "Genel Bakış" },
  { href: "/reservations", label: "Rezervasyonlar" },
  { href: "/reports", label: "Raporlar" },
] as const;

export function AppShell({ children, currentRoute }: AppShellProps) {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-eyebrow">Otel Gelmeme Tahmin Sistemi</span>
          <span className="brand-title">Operasyon Ekranı</span>
          <span className="brand-subtitle">
            Riskli rezervasyonları izlemek, operasyon sırasını görmek ve günlük takibi tek yerden yürütmek için
            hazırlanmış iç kullanım ekranı.
          </span>
        </div>

        <nav className="nav-grid" aria-label="Ana gezinme">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${item.href === currentRoute ? "nav-link-active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      {children}
    </main>
  );
}

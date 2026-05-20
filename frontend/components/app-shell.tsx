import Link from "next/link";

type AppShellProps = {
  children: React.ReactNode;
  currentRoute: "/dashboard" | "/customer-risk" | "/reservation-risk" | "/reservations" | "/reports";
};

const navigation = [
  { href: "/dashboard", label: "Genel Bakış" },
  { href: "/customer-risk", label: "Müşteri Ön Kontrolü" },
  { href: "/reservation-risk", label: "Saf No-show" },
  { href: "/reservations", label: "Arama Havuzu" },
  { href: "/reports", label: "Raporlar" },
] as const;

export function AppShell({ children, currentRoute }: AppShellProps) {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-eyebrow">Otel Gerçekleşmeme Riski</span>
          <span className="brand-title">Günlük Takip Ekranı</span>
          <span className="brand-subtitle">
            İptal veya no-show riski taşıyan rezervasyonları tek kuyrukta izlemek, misafir takibini planlamak ve
            kapasite kararlarını desteklemek için hazırlanmış iç operasyon ekranı.
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

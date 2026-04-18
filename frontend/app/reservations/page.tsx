import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { RiskBadge } from "@/components/risk-badge";
import { getReservations } from "@/lib/api";
import { formatPropertyLabel, formatRiskLabel } from "@/lib/presentation";

type ReservationsPageProps = {
  searchParams?: Promise<{
    property_id?: string;
    distribution_channel?: string;
    risk_class?: string;
    date_from?: string;
    date_to?: string;
  }>;
};

export default async function ReservationsPage({ searchParams }: ReservationsPageProps) {
  const filters = (await searchParams) ?? {};
  const reservations = await getReservations(filters);

  return (
    <AppShell currentRoute="/reservations">
      <div className="page-grid">
        <PageHeader
          title="Rezervasyonlar"
          description="Manuel inceleme, kanal takibi ve günlük operasyon sırası için filtrelenebilir çalışma listesi."
          badges={["Filtrelenebilir kuyruk", `${reservations.total} kayıt görüntüleniyor`, "Detay görünümü hazır"]}
        />

        <PanelCard title="Filtreler" subtitle="Sayfa filtreleri doğrudan API sorgu parametrelerine bağlanır.">
          <form className="filters" method="get">
            <div className="field">
              <label htmlFor="property_id">Otel</label>
              <select id="property_id" name="property_id" defaultValue={filters.property_id ?? ""}>
                <option value="">Tüm oteller</option>
                {reservations.filters.property_ids.map((propertyId) => (
                  <option key={propertyId} value={propertyId}>
                    {formatPropertyLabel(propertyId)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="distribution_channel">Rezervasyon kanalı</label>
              <select
                id="distribution_channel"
                name="distribution_channel"
                defaultValue={filters.distribution_channel ?? ""}
              >
                <option value="">Tüm kanallar</option>
                {reservations.filters.distribution_channels.map((channel) => (
                  <option key={channel} value={channel}>
                    {channel}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="risk_class">Risk seviyesi</label>
              <select id="risk_class" name="risk_class" defaultValue={filters.risk_class ?? ""}>
                <option value="">Tümü</option>
                {reservations.filters.risk_classes.map((riskClass) => (
                  <option key={riskClass} value={riskClass}>
                    {formatRiskLabel(riskClass)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="date_from">Giriş tarihi başlangıç</label>
              <input
                id="date_from"
                name="date_from"
                type="date"
                defaultValue={filters.date_from}
                min={reservations.filters.min_arrival_date ?? undefined}
                max={reservations.filters.max_arrival_date ?? undefined}
              />
            </div>
            <div className="field">
              <label htmlFor="date_to">Giriş tarihi bitiş</label>
              <input
                id="date_to"
                name="date_to"
                type="date"
                defaultValue={filters.date_to}
                min={reservations.filters.min_arrival_date ?? undefined}
                max={reservations.filters.max_arrival_date ?? undefined}
              />
            </div>
            <div className="field">
              <label htmlFor="apply_filters">Filtreleri uygula</label>
              <button id="apply_filters" type="submit" className="button">
                Listeyi yenile
              </button>
            </div>
          </form>
        </PanelCard>

        <PanelCard title="Kuyruk Özeti" subtitle="Operasyon ekranında yalnızca son skorlanan rezervasyonlar gösterilir.">
          <div className="summary-band">
            <div className="summary-cell">
              Görünen kayıt
              <strong>{reservations.total}</strong>
            </div>
            <div className="summary-cell">
              Risk seçenekleri
              <strong>{reservations.filters.risk_classes.map((riskClass) => formatRiskLabel(riskClass)).join(", ")}</strong>
            </div>
            <div className="summary-cell">
              Tarih aralığı
              <strong>
                {reservations.filters.min_arrival_date ?? "-"} - {reservations.filters.max_arrival_date ?? "-"}
              </strong>
            </div>
          </div>
        </PanelCard>

        <PanelCard title="Çalışma Kuyruğu" subtitle="Rezervasyon satırları detay görünümü ve günlük takip için hazırdır.">
          {reservations.items.length === 0 ? (
            <div className="empty-state">
              Seçili filtrelerle eşleşen rezervasyon bulunamadı. Veri aktarımı ve tahminler geldikçe bu liste
              dolacaktır.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Rezervasyon</th>
                  <th>Otel</th>
                  <th>Giriş</th>
                  <th>Kanal</th>
                  <th>Müşteri tipi</th>
                  <th>Risk</th>
                  <th>Skor</th>
                  <th className="table-actions">Detay</th>
                </tr>
              </thead>
              <tbody>
                {reservations.items.map((item) => (
                  <tr key={item.reservation_id}>
                    <td>
                      <Link className="table-link" href={`/reservations/${item.reservation_id}`}>
                        #{item.reservation_id}
                      </Link>
                    </td>
                    <td>{formatPropertyLabel(item.property_id)}</td>
                    <td>{item.arrival_date ?? "Belirsiz"}</td>
                    <td>{item.distribution_channel ?? "Bilinmiyor"}</td>
                    <td>{item.customer_type ?? "Bilinmiyor"}</td>
                    <td>
                      <RiskBadge riskClass={item.risk_class} />
                    </td>
                    <td className="table-score">{item.score?.toFixed(3) ?? "-"}</td>
                    <td className="table-actions">
                      <Link className="table-link" href={`/reservations/${item.reservation_id}`}>
                        Gör
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </PanelCard>
      </div>
    </AppShell>
  );
}

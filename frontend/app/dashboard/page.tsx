import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { RiskBadge } from "@/components/risk-badge";
import { getBenchmarkReport, getDashboardSummary } from "@/lib/api";
import { formatDataSourceLabel, formatPropertyLabel } from "@/lib/presentation";

const DEFAULT_ACTION_THRESHOLD = 0.4;

export default async function DashboardPage() {
  const [summary, report] = await Promise.all([getDashboardSummary(), getBenchmarkReport()]);
  const recommendedModel = report.recommended_model ?? summary.kpis.active_model_name ?? "pending";
  const topKRows = recommendedModel ? report.top_k_tables[recommendedModel] ?? [] : [];
  const thresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const top50 = topKRows.find((row) => row.segment === "top_50");
  const actionThreshold = report.selected_threshold ?? DEFAULT_ACTION_THRESHOLD;
  const thresholdSnapshot =
    thresholdRows.find((row) => Math.abs(row.threshold - actionThreshold) < 0.0001) ?? thresholdRows[0];
  const callPoolSize = thresholdSnapshot?.actioned_count ?? summary.items.length;
  const top100 = topKRows.find((row) => row.segment === "top_100");

  return (
    <AppShell currentRoute="/dashboard">
      <div className="page-grid">
        <PageHeader
          title="Operasyon Özeti"
          description="Bugün aranacak veya kontrol edilecek rezervasyon havuzu. Amaç teknik skoru göstermek değil, resepsiyon ve rezervasyon ekibinin sıradaki işi net görmesi."
          badges={[
            "Günlük takip",
            `İlk ${summary.items.length} riskli kayıt`,
            formatDataSourceLabel(summary.data_source),
          ]}
        />

        <section className="metric-grid">
          <MetricCard label="Toplam rezervasyon" value={summary.kpis.total_reservations.toString()} />
          <MetricCard label="Takip havuzu" value={callPoolSize.toString()} hint="Takip sınırının üstündeki kayıtlar" />
          <MetricCard label="Yüksek takip önceliği" value={summary.kpis.high_risk_reservations.toString()} />
          <MetricCard label="Orta takip önceliği" value={summary.kpis.medium_risk_reservations.toString()} />
          <MetricCard label="Açık takip" value={summary.kpis.action_pending_count.toString()} />
          <MetricCard label="Tamamlanan" value={summary.kpis.action_completed_count.toString()} />
          <MetricCard label="Takip gerekli" value={summary.kpis.action_follow_up_count.toString()} />
        </section>

        <div className="grid-two">
          <PanelCard title="Bugünkü Arama Planı" subtitle="Kuyruk büyüklüğü ve beklenen isabet oranı.">
            <div className="summary-band">
              <div className="summary-cell">
                Aranacak havuz
                <strong>{callPoolSize}</strong>
              </div>
              <div className="summary-cell">
                Takip isabeti
                <strong>{thresholdSnapshot ? `${(thresholdSnapshot.precision * 100).toFixed(1)}%` : "-"}</strong>
              </div>
              <div className="summary-cell">
                Sorunlu rezervasyon yakalama
                <strong>{thresholdSnapshot ? `${(thresholdSnapshot.recall * 100).toFixed(1)}%` : "-"}</strong>
              </div>
              <div className="summary-cell">
                İlk 100 kayıtta
                <strong>{top100 ? `${top100.captured_no_show} kayıt` : "-"}</strong>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Ekip Notu" subtitle="Takip sırasında kullanılacak sade yorum.">
            <div className="stack">
              <p className="subtle">
                Bu kuyruk, iptal veya no-show ihtimali yüksek rezervasyonları önce aramak için hazırlanır. İlk sıradaki
                kayıtlar için varış teyidi, ödeme/garanti kontrolü ve gerekirse depozito takibi yapılmalıdır.
              </p>
              <div className="summary-band">
                <div className="summary-cell">
                  Liste durumu
                  <strong>{summary.kpis.latest_scored_at ? "Güncel" : "Bekleniyor"}</strong>
                </div>
                <div className="summary-cell">
                  Kayıt modu
                  <strong>{summary.action_support_enabled ? "Takip kaydı açılabilir" : "Sadece görüntüleme"}</strong>
                </div>
                <div className="summary-cell">
                  Son güncelleme
                  <strong>{summary.kpis.latest_scored_at ? new Date(summary.kpis.latest_scored_at).toLocaleDateString("tr-TR") : "-"}</strong>
                </div>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="Aranacak İlk Rezervasyonlar" subtitle="İptal veya no-show riski en yüksek kayıtlar önce listelenir.">
          {summary.items.length === 0 ? (
            <div className="empty-state">
              Henüz riskli kayıt görünmüyor. Tahmin çıktıları hazır olduğunda bu alan otomatik olarak dolacak.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Rezervasyon</th>
                  <th>Otel</th>
                  <th>Giriş</th>
                  <th>Kanal</th>
                  <th>Risk</th>
                  <th>Öncelik puanı</th>
                  <th className="table-actions">Detay</th>
                </tr>
              </thead>
              <tbody>
                {summary.items.map((item) => (
                  <tr key={item.reservation_id}>
                    <td>
                      <Link className="table-link" href={`/reservations/${item.reservation_id}`}>
                        #{item.reservation_id}
                      </Link>
                    </td>
                    <td>{formatPropertyLabel(item.property_id)}</td>
                    <td>{item.arrival_date ?? "Belirsiz"}</td>
                    <td>{item.distribution_channel ?? "Bilinmiyor"}</td>
                    <td>
                      <RiskBadge riskClass={item.risk_class} />
                    </td>
                    <td className="table-score">{item.score?.toFixed(3) ?? "-"}</td>
                    <td className="table-actions">
                      <Link className="table-link" href={`/reservations/${item.reservation_id}`}>
                        Aç
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

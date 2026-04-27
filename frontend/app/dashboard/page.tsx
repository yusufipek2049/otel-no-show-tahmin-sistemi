import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { RiskBadge } from "@/components/risk-badge";
import { getBenchmarkReport, getDashboardSummary } from "@/lib/api";
import { formatDataSourceLabel, formatPropertyLabel } from "@/lib/presentation";

export default async function DashboardPage() {
  const [summary, report] = await Promise.all([getDashboardSummary(), getBenchmarkReport()]);
  const recommendedModel = report.recommended_model ?? summary.kpis.active_model_name ?? "pending";
  const topKRows = recommendedModel ? report.top_k_tables[recommendedModel] ?? [] : [];
  const thresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const top50 = topKRows.find((row) => row.segment === "top_50");
  const actionThreshold = report.selected_threshold ?? 0.35;
  const thresholdSnapshot =
    thresholdRows.find((row) => Math.abs(row.threshold - actionThreshold) < 0.0001) ?? thresholdRows[0];

  return (
    <AppShell currentRoute="/dashboard">
      <div className="page-grid">
        <PageHeader
          title="Operasyon Özeti"
          description="Güncel risk sinyalleri, skorlama yoğunluğu ve manuel inceleme sırasındaki rezervasyonlar."
          badges={[
            "İç operasyon ekranı",
            `${summary.items.length} riskli kayıt`,
            formatDataSourceLabel(summary.data_source),
          ]}
        />

        <section className="metric-grid">
          <MetricCard label="Toplam rezervasyon" value={summary.kpis.total_reservations.toString()} />
          <MetricCard label="Yüksek risk" value={summary.kpis.high_risk_reservations.toString()} />
          <MetricCard label="Orta risk" value={summary.kpis.medium_risk_reservations.toString()} />
          <MetricCard label="Açık aksiyon" value={summary.kpis.action_pending_count.toString()} />
          <MetricCard label="Tamamlanan" value={summary.kpis.action_completed_count.toString()} />
          <MetricCard label="Takip gerekli" value={summary.kpis.action_follow_up_count.toString()} />
          <MetricCard
            label="Son skor durumu"
            value={summary.kpis.latest_scored_at ? "Hazır" : "Bekleniyor"}
            hint={summary.kpis.latest_scored_at ?? "Henüz skorlama yapılmadı"}
          />
        </section>

        <div className="grid-two">
          <PanelCard title="Aksiyon Özeti" subtitle="Güncel eşik ve operasyon kuyruğundan türetilen kısa görünüm.">
            <div className="summary-band">
              <div className="summary-cell">
                Eşik
                <strong>{(report.selected_threshold ?? 0).toFixed(2)}</strong>
              </div>
              <div className="summary-cell">
                Eşikte kesinlik
                <strong>{thresholdSnapshot ? `${(thresholdSnapshot.precision * 100).toFixed(1)}%` : "-"}</strong>
              </div>
              <div className="summary-cell">
                Eşikte duyarlılık
                <strong>{thresholdSnapshot ? `${(thresholdSnapshot.recall * 100).toFixed(1)}%` : "-"}</strong>
              </div>
              <div className="summary-cell">
                İlk 50'de yakalama
                <strong>{top50 ? `${(top50.recall * 100).toFixed(1)}%` : "-"}</strong>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Operasyon Notu" subtitle="Karar desteği için kısa açıklama.">
            <div className="stack">
              <p className="subtle">
                {report.recommendation_reason ??
                  "Henüz değerlendirme çıktısı yok. Eğitim hattı çalıştığında bu alan otomatik olarak dolacak."}
              </p>
              <div className="summary-band">
                <div className="summary-cell">
                  Skorlama kaynağı
                  <strong>{formatDataSourceLabel(summary.data_source)}</strong>
                </div>
                <div className="summary-cell">
                  Skorlama modu
                  <strong>{summary.scoring_status}</strong>
                </div>
                <div className="summary-cell">
                  Aksiyon akışı
                  <strong>{summary.action_support_enabled ? "Yazılabilir" : "Read-only"}</strong>
                </div>
              </div>
              <div className="section-note">
                <span className="tag">Not</span>
                <span className="mono">Bu ekranda model adı gösterilmez.</span>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="Son Riskli Rezervasyonlar" subtitle="Her rezervasyon için son skor kaydına göre listelenir.">
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
                  <th>Skor</th>
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

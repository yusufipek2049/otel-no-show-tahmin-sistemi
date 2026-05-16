import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { getBenchmarkReport } from "@/lib/api";
import { formatCandidateLabel, formatMetricLabel, formatTopKSegmentLabel } from "@/lib/presentation";

export default async function ReservationRiskPage() {
  const report = await getBenchmarkReport("reservation_post_booking");
  const recommendedModel = report.recommended_model ?? report.comparison[0]?.model_name ?? null;
  const thresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const topKRows = recommendedModel ? report.top_k_tables[recommendedModel] ?? [] : [];
  const selectedThreshold =
    report.selected_threshold && thresholdRows.length > 0
      ? thresholdRows.find((row) => Math.abs(row.threshold - report.selected_threshold!) < 0.0001) ?? thresholdRows[0]
      : thresholdRows[0];
  const top50 = topKRows.find((row) => row.segment === "top_50");

  return (
    <AppShell currentRoute="/reservation-risk">
      <div className="page-grid">
        <PageHeader
          title="Rezervasyon No-show Riski"
          description="Rezervasyon oluştuktan sonra ödeme denemeleri, iletişim yanıtları, kampanya ve garanti/depozito sinyalleriyle güncellenen risk görünümü."
          badges={["reservation_post_booking", report.selected_threshold ? `Eşik ${report.selected_threshold.toFixed(2)}` : "Eşik yok"]}
        />

        <section className="metric-grid">
          <MetricCard label="Aktif model" value={report.comparison.length > 0 ? "Hazır" : "Bekleniyor"} />
          <MetricCard label="Eşik kesinliği" value={selectedThreshold ? `${(selectedThreshold.precision * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="Eşik duyarlılığı" value={selectedThreshold ? `${(selectedThreshold.recall * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="İlk 50 yakalama" value={top50 ? `${(top50.recall * 100).toFixed(1)}%` : "-"} />
        </section>

        <PanelCard title="Rezervasyon Model Durumu" subtitle="CatBoost, logistic regression skorunu ek operasyonel sinyal olarak kullanır.">
          {report.comparison.length === 0 ? (
            <div className="empty-state">Bu stage için eğitim artifact'i henüz yok.</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>PR-AUC</th>
                  <th>ROC-AUC</th>
                  <th>Kesinlik</th>
                  <th>Duyarlılık</th>
                  <th>F1</th>
                  <th>Brier</th>
                </tr>
              </thead>
              <tbody>
                {report.comparison.map((row, index) => (
                  <tr key={row.model_name}>
                    <td>{formatCandidateLabel(index)}</td>
                    <td className="table-score">{row.pr_auc?.toFixed(3) ?? "-"}</td>
                    <td className="table-score">{row.roc_auc?.toFixed(3) ?? "-"}</td>
                    <td className="table-score">{row.precision?.toFixed(3) ?? "-"}</td>
                    <td className="table-score">{row.recall?.toFixed(3) ?? "-"}</td>
                    <td className="table-score">{row.f1?.toFixed(3) ?? "-"}</td>
                    <td className="table-score">{row.brier_score?.toFixed(3) ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </PanelCard>

        <div className="grid-two">
          <PanelCard title="Eşik Tablosu" subtitle="Rezervasyon aksiyon eşiği 0.90 olarak uygulanır.">
            {thresholdRows.length === 0 ? (
              <div className="empty-state">Henüz eşik metriği yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Eşik</th>
                    <th>Kesinlik</th>
                    <th>Duyarlılık</th>
                    <th>Aksiyona alınan</th>
                  </tr>
                </thead>
                <tbody>
                  {thresholdRows.map((row) => (
                    <tr key={row.threshold}>
                      <td className="table-score">{row.threshold.toFixed(2)}</td>
                      <td className="table-score">{row.precision.toFixed(3)}</td>
                      <td className="table-score">{row.recall.toFixed(3)}</td>
                      <td className="table-score">{row.actioned_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>

          <PanelCard title="Top-K Yakalama" subtitle="Operasyon kuyruğu boyutuna göre yakalanan no-show oranı.">
            {topKRows.length === 0 ? (
              <div className="empty-state">Henüz top-k metriği yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Dilim</th>
                    <th>Seçilen</th>
                    <th>Yakalanan</th>
                    <th>Duyarlılık</th>
                  </tr>
                </thead>
                <tbody>
                  {topKRows.map((row) => (
                    <tr key={row.segment}>
                      <td>{formatTopKSegmentLabel(row.segment)}</td>
                      <td className="table-score">{row.selected_count}</td>
                      <td className="table-score">{row.captured_no_show}</td>
                      <td className="table-score">{row.recall.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>
        </div>

        <PanelCard title="Kullanılan Sinyal Grupları" subtitle="Bu stage rezervasyon sonrası oluşan sentetik operasyonel sinyalleri içerir.">
          <div className="badge-row">
            {["müşteri kimliği", "ödeme başarısızlığı", "iletişim geçmişi", "son dakika davranışı", "kanal kampanyası", "garanti/depozito detayı"].map(
              (label) => (
                <span key={label} className="pill">
                  {label}
                </span>
              ),
            )}
          </div>
        </PanelCard>
      </div>
    </AppShell>
  );
}

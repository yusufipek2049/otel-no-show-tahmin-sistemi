import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { getBenchmarkReport } from "@/lib/api";
import { formatCandidateLabel, formatMetricLabel, formatStatusLabel } from "@/lib/presentation";

export default async function CustomerRiskPage() {
  const report = await getBenchmarkReport("customer_pre_reservation");
  const recommendedModel = report.recommended_model ?? report.comparison[0]?.model_name ?? null;
  const thresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const selectedThreshold =
    report.selected_threshold && thresholdRows.length > 0
      ? thresholdRows.find((row) => Math.abs(row.threshold - report.selected_threshold!) < 0.0001) ?? thresholdRows[0]
      : thresholdRows[0];

  return (
    <AppShell currentRoute="/customer-risk">
      <div className="page-grid">
        <PageHeader
          title="Müşteri Ön Kontrolü"
          description="Rezervasyon kesinleşmeden önce müşterinin geçmiş davranışı, ödeme durumu ve iletişim sinyalleriyle takip önceliği verir."
          badges={["Ön rezervasyon", report.selected_threshold ? `Takip sınırı ${report.selected_threshold.toFixed(2)}` : "Takip sınırı yok"]}
        />

        <section className="metric-grid">
          <MetricCard label="Durum" value={report.comparison.length > 0 ? "Hazır" : "Bekleniyor"} />
          <MetricCard label="Kullanılan yöntem" value={recommendedModel ? formatCandidateLabel(0) : "-"} />
          <MetricCard label="Takip isabeti" value={selectedThreshold ? `${(selectedThreshold.precision * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="Sorunlu kayıt yakalama" value={selectedThreshold ? `${(selectedThreshold.recall * 100).toFixed(1)}%` : "-"} />
        </section>

        <PanelCard title="Kalite Özeti" subtitle="Bu görünüm, müşteriyi rezervasyon kesinleşmeden önce daha dikkatli kontrol etmek için kullanılır.">
          {report.comparison.length === 0 ? (
            <div className="empty-state">Bu görünüm için henüz eğitim çıktısı yok.</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Yöntem</th>
                  <th>Öncelik kalitesi</th>
                  <th>Ayrıştırma gücü</th>
                  <th>İsabet</th>
                  <th>Yakalama</th>
                  <th>Denge</th>
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
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </PanelCard>

        <PanelCard title="Teknik Durum" subtitle="İç değerlendirme için tutulan kısa model notları.">
          <div className="status-list">
            {report.models.map((model, index) => (
              <article key={model.model_name} className="status-item">
                <h3>{formatCandidateLabel(index)}</h3>
                <p className="muted">{model.notes}</p>
                <div className="badge-row">
                  <span className="pill">Durum: {formatStatusLabel(model.status)}</span>
                  {model.metrics.map((metric) => (
                    <span key={`${model.model_name}-${metric.name}`} className="pill">
                      {formatMetricLabel(metric.name)}:{" "}
                      {metric.value !== null ? metric.value.toFixed(3) : formatStatusLabel(metric.status)}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </PanelCard>
      </div>
    </AppShell>
  );
}

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
          title="Müşteri No-show Riski"
          description="Rezervasyon kesinleşmeden önce müşteri kimliği, geçmiş davranış, ödeme ve iletişim sinyallerinden üretilen risk görünümü."
          badges={["customer_pre_reservation", report.selected_threshold ? `Eşik ${report.selected_threshold.toFixed(2)}` : "Eşik yok"]}
        />

        <section className="metric-grid">
          <MetricCard label="Aktif model" value={report.comparison.length > 0 ? "Hazır" : "Bekleniyor"} />
          <MetricCard label="Skor mimarisi" value={recommendedModel ? formatCandidateLabel(0) : "-"} />
          <MetricCard label="Eşik kesinliği" value={selectedThreshold ? `${(selectedThreshold.precision * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="Eşik duyarlılığı" value={selectedThreshold ? `${(selectedThreshold.recall * 100).toFixed(1)}%` : "-"} />
        </section>

        <PanelCard title="Müşteri Model Durumu" subtitle="Logistic Regression skoru CatBoost modeline besleyici sinyal olarak verilir.">
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

        <PanelCard title="Model Artifact Durumu" subtitle="Müşteri düzeyi model artifact'lerinden gelen kısa durum.">
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

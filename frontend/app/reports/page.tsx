import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { getBenchmarkReport } from "@/lib/api";
import { formatCandidateLabel, formatMetricLabel, formatStatusLabel, formatTopKSegmentLabel } from "@/lib/presentation";

export default async function ReportsPage() {
  const report = await getBenchmarkReport();
  const recommendedModel = report.recommended_model ?? report.comparison[0]?.model_name ?? null;
  const recommendedThresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const recommendedTopKRows = recommendedModel ? report.top_k_tables[recommendedModel] ?? [] : [];
  const top50 = recommendedTopKRows.find((row) => row.segment === "top_50");

  return (
    <AppShell currentRoute="/reports">
      <div className="page-grid">
        <PageHeader
          title="Raporlar"
          description="Son değerlendirme çıktısından türetilen karşılaştırma, eşik ve operasyon yakalama özetleri."
          badges={[
            report.selected_threshold ? `Eşik ${report.selected_threshold.toFixed(2)}` : "Eşik yok",
            ...report.primary_metrics.map((metric) => formatMetricLabel(metric)),
          ]}
        />

        <div className="grid-three">
          <PanelCard title="Veri Bölme Stratejisi" subtitle="Proje dokümanları ve veri sızıntısına karşı güvenli modelleme planıyla uyumlu.">
            <p className="muted">{report.split_strategy}</p>
          </PanelCard>

          <PanelCard title="Yorum" subtitle="Çıktıların kısa operasyon özeti.">
            <div className="stack">
              <p className="muted">{report.recommendation_reason ?? "Henüz yorum üretilecek bir değerlendirme sonucu yok."}</p>
              <div className="section-note">
                <span className="tag">Gizlilik</span>
                <span className="mono">Bu ekranda model adı paylaşılmaz.</span>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Operasyon Özeti" subtitle="Karar sırasında en çok kullanılan ölçüler öne çıkarılır.">
            <div className="summary-band">
              <div className="summary-cell">
                İlk 50 yakalama
                <strong>{top50 ? `${(top50.recall * 100).toFixed(1)}%` : "-"}</strong>
              </div>
              <div className="summary-cell">
                Eşik satırı
                <strong>{recommendedThresholdRows.length}</strong>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="Karşılaştırma Özeti" subtitle="Güncel adaylar arasındaki temel performans görünümü.">
          {report.comparison.length === 0 ? (
            <div className="empty-state">Henüz karşılaştırma satırı bulunmuyor.</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Aday</th>
                  <th>PR-AUC</th>
                  <th>ROC-AUC</th>
                  <th>Eşikte kesinlik</th>
                  <th>Eşikte duyarlılık</th>
                  <th>Eşikte F1</th>
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
          <PanelCard
            title="Eşik Tablosu"
            subtitle="Tanımlı kesim noktalarındaki kesinlik, duyarlılık ve aksiyon hacmi."
          >
            {recommendedThresholdRows.length === 0 ? (
              <div className="empty-state">Henüz eşik metriği yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Eşik</th>
                    <th>Kesinlik</th>
                    <th>Duyarlılık</th>
                    <th>F1</th>
                    <th>Aksiyona alınan</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendedThresholdRows.map((row) => (
                    <tr key={`${recommendedModel}-${row.threshold}`}>
                      <td className="table-score">{row.threshold.toFixed(2)}</td>
                      <td className="table-score">{row.precision.toFixed(3)}</td>
                      <td className="table-score">{row.recall.toFixed(3)}</td>
                      <td className="table-score">{row.f1.toFixed(3)}</td>
                      <td className="table-score">{row.actioned_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>

          <PanelCard
            title="Top-K Yakalama"
            subtitle="Sabit kuyruk boyutları ve yüzde dilimlerinde operasyon yakalama görünümü."
          >
            {recommendedTopKRows.length === 0 ? (
              <div className="empty-state">Henüz top-k özeti yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Dilim</th>
                    <th>Seçilen</th>
                    <th>Yakalanan gelmeme</th>
                    <th>Toplam gelmeme</th>
                    <th>Duyarlılık</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendedTopKRows.map((row) => (
                    <tr key={`${recommendedModel}-${row.segment}`}>
                      <td>{formatTopKSegmentLabel(row.segment)}</td>
                      <td className="table-score">{row.selected_count}</td>
                      <td className="table-score">{row.captured_no_show}</td>
                      <td className="table-score">{row.total_no_show}</td>
                      <td className="table-score">{row.recall.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>
        </div>

        <PanelCard title="Aday Durumları" subtitle="Hızlı tarama için kısa durum kartları.">
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

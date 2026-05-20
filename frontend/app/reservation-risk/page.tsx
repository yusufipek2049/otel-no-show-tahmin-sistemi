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
          title="Saf No-show Görünümü"
          description="İptalleri dışarıda bırakan dar takip görünümü. Ana operasyon havuzundan farklı olarak sadece gelmeyen rezervasyonlara odaklanır."
          badges={["Sadece no-show", report.selected_threshold ? `Takip sınırı ${report.selected_threshold.toFixed(2)}` : "Takip sınırı yok"]}
        />

        <section className="metric-grid">
          <MetricCard label="Durum" value={report.comparison.length > 0 ? "Hazır" : "Bekleniyor"} />
          <MetricCard label="Takip isabeti" value={selectedThreshold ? `${(selectedThreshold.precision * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="No-show yakalama" value={selectedThreshold ? `${(selectedThreshold.recall * 100).toFixed(1)}%` : "-"} />
          <MetricCard label="İlk 50 yakalama" value={top50 ? `${(top50.recall * 100).toFixed(1)}%` : "-"} />
        </section>

        <PanelCard title="Dar Hedef Özeti" subtitle="Bu ekran teknik kontrol içindir; günlük takipte ana gerçekleşmeme havuzu kullanılmalıdır.">
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
                  <th>Olasılık hatası</th>
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
          <PanelCard title="Takip Sınırı Tablosu" subtitle="Sınır düştükçe daha çok rezervasyon listeye girer; isabet ve yakalama birlikte okunmalıdır.">
            {thresholdRows.length === 0 ? (
              <div className="empty-state">Henüz takip sınırı özeti yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Sınır</th>
                    <th>İsabet</th>
                    <th>Yakalama</th>
                    <th>Listeye giren</th>
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

          <PanelCard title="Liste Boyutuna Göre Yakalama" subtitle="Arama listesi büyüdükçe yakalanan no-show oranını gösterir.">
            {topKRows.length === 0 ? (
              <div className="empty-state">Henüz liste boyutu özeti yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Dilim</th>
                    <th>Seçilen</th>
                    <th>Yakalanan</th>
                    <th>Yakalama</th>
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

        <PanelCard title="Kullanılan İşaretler" subtitle="Rezervasyon sonrasında oluşan operasyonel bilgilerin ana grupları.">
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

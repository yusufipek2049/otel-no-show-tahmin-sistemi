import { AppShell } from "@/components/app-shell";
import { CaptureBarChart, ChannelRiskChart, TrendLineChart } from "@/components/charts";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import {
  getActionEffectiveness,
  getBenchmarkReport,
  getChannelBreakdown,
  getNoShowTrends,
  getOperationsSummary,
  getSegmentBreakdown,
} from "@/lib/api";
import {
  formatCandidateLabel,
  formatDataSourceLabel,
  formatMetricLabel,
  formatStatusLabel,
  formatTopKSegmentLabel,
} from "@/lib/presentation";

export default async function ReportsPage() {
  const [report, operationsSummary, noShowTrends, channelBreakdown, segmentBreakdown, actionEffectiveness] =
    await Promise.all([
      getBenchmarkReport(),
      getOperationsSummary(),
      getNoShowTrends(),
      getChannelBreakdown(),
      getSegmentBreakdown(),
      getActionEffectiveness(),
    ]);
  const recommendedModel = report.recommended_model ?? report.comparison[0]?.model_name ?? null;
  const recommendedThresholdRows = recommendedModel ? report.threshold_tables[recommendedModel] ?? [] : [];
  const recommendedTopKRows = recommendedModel ? report.top_k_tables[recommendedModel] ?? [] : [];
  const top50 = recommendedTopKRows.find((row) => row.segment === "top_50");

  return (
    <AppShell currentRoute="/reports">
      <div className="page-grid">
        <PageHeader
          title="Raporlar"
          description="Gerçekleşmeme riski, kanal kırılımları, segment kırılımları ve takip havuzu birlikte sunulur."
          badges={[
            formatDataSourceLabel(operationsSummary.data_source),
            report.selected_threshold ? `Takip sınırı ${report.selected_threshold.toFixed(2)}` : "Takip sınırı yok",
            ...report.primary_metrics.map((metric) => formatMetricLabel(metric)),
          ]}
        />

        <PanelCard title="Yönetim Özeti" subtitle="İptal veya no-show ile tamamlanmayan rezervasyonların yönetim görünümü.">
          <div className="summary-band">
            <div className="summary-cell">
              Toplam rezervasyon
              <strong>{operationsSummary.total_reservations}</strong>
            </div>
            <div className="summary-cell">
              Gerçekleşmeme oranı
              <strong>{(operationsSummary.no_show_rate * 100).toFixed(1)}%</strong>
            </div>
            <div className="summary-cell">
              İptal oranı
              <strong>{(operationsSummary.cancellation_rate * 100).toFixed(1)}%</strong>
            </div>
            <div className="summary-cell">
              Yüksek risk
              <strong>{operationsSummary.high_risk_reservations}</strong>
            </div>
            <div className="summary-cell">
              Açık takip
              <strong>{operationsSummary.action_pending_count}</strong>
            </div>
            <div className="summary-cell">
              Tamamlanan takip
              <strong>{operationsSummary.action_completed_count}</strong>
            </div>
          </div>
          {operationsSummary.note ? <p className="table-caption muted">{operationsSummary.note}</p> : null}
        </PanelCard>

        <div className="grid-two">
          <PanelCard title="Gerçekleşmeme Trendi" subtitle="Aylık bazda gerçekleşmeme ve iptal oranı.">
            {noShowTrends.length === 0 ? (
              <div className="empty-state">Henüz trend verisi yok.</div>
            ) : (
              <div className="stack">
                <TrendLineChart points={noShowTrends} />
                <table className="table">
                  <thead>
                    <tr>
                      <th>Dönem</th>
                      <th>Rezervasyon</th>
                      <th>Gerçekleşmeme</th>
                      <th>İptal</th>
                      <th>Gerçekleşmeme oranı</th>
                    </tr>
                  </thead>
                  <tbody>
                    {noShowTrends.map((row) => (
                      <tr key={row.period}>
                        <td>{row.period}</td>
                        <td className="table-score">{row.total_reservations}</td>
                        <td className="table-score">{row.no_show_count}</td>
                        <td className="table-score">{row.canceled_count}</td>
                        <td className="table-score">{(row.no_show_rate * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </PanelCard>

          <PanelCard title="Takip Kapsamı" subtitle="Arama, mesaj ve garanti kontrollerinin genel görünümü.">
            <div className="summary-band">
              <div className="summary-cell">
                Toplam takip kaydı
                <strong>{actionEffectiveness.total_actions}</strong>
              </div>
              <div className="summary-cell">
                Açık
                <strong>{actionEffectiveness.open_actions}</strong>
              </div>
              <div className="summary-cell">
                Takipte
                <strong>{actionEffectiveness.follow_up_actions}</strong>
              </div>
              <div className="summary-cell">
                Takip açılan yüksek risk
                <strong>{actionEffectiveness.high_risk_with_action_count}</strong>
              </div>
            </div>
            {actionEffectiveness.note ? <p className="table-caption muted">{actionEffectiveness.note}</p> : null}
          </PanelCard>
        </div>

        <div className="grid-two">
          <PanelCard title="Kanal Bazlı Kırılım" subtitle="Rezervasyon kanallarında gerçekleşmeme yükü ve yüksek risk yoğunluğu.">
            {channelBreakdown.length === 0 ? (
              <div className="empty-state">Henüz kanal kırılımı yok.</div>
            ) : (
              <div className="stack">
                <ChannelRiskChart rows={channelBreakdown} />
                <table className="table">
                  <thead>
                    <tr>
                      <th>Kanal</th>
                      <th>Rezervasyon</th>
                      <th>Yüksek risk</th>
                      <th>Gerçekleşmeme oranı</th>
                      <th>Ortalama puan</th>
                    </tr>
                  </thead>
                  <tbody>
                    {channelBreakdown.map((row) => (
                      <tr key={row.dimension_value}>
                        <td>{row.dimension_value}</td>
                        <td className="table-score">{row.total_reservations}</td>
                        <td className="table-score">{row.high_risk_reservations}</td>
                        <td className="table-score">{(row.no_show_rate * 100).toFixed(1)}%</td>
                        <td className="table-score">{row.average_score?.toFixed(3) ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </PanelCard>

          <PanelCard title="Segment Bazlı Kırılım" subtitle="Pazar segmentlerinde risk ve gerçekleşen sonuç görünümü.">
            {segmentBreakdown.length === 0 ? (
              <div className="empty-state">Henüz segment kırılımı yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Segment</th>
                    <th>Rezervasyon</th>
                    <th>Gerçekleşmeme</th>
                    <th>İptal</th>
                    <th>Gerçekleşmeme oranı</th>
                  </tr>
                </thead>
                <tbody>
                  {segmentBreakdown.map((row) => (
                    <tr key={row.dimension_value}>
                      <td>{row.dimension_value}</td>
                      <td className="table-score">{row.total_reservations}</td>
                      <td className="table-score">{row.no_show_count}</td>
                      <td className="table-score">{row.canceled_count}</td>
                      <td className="table-score">{(row.no_show_rate * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>
        </div>

        <div className="grid-three">
          <PanelCard title="Arama Havuzu" subtitle="Takip sınırının üstündeki kayıtlar günlük listeye girer.">
            <div className="summary-band">
              <div className="summary-cell">
                Havuz büyüklüğü
                <strong>{recommendedThresholdRows[0]?.actioned_count ?? "-"}</strong>
              </div>
              <div className="summary-cell">
                Beklenen isabet
                <strong>{recommendedThresholdRows[0] ? `${(recommendedThresholdRows[0].precision * 100).toFixed(1)}%` : "-"}</strong>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Yorum" subtitle="Yönetici için kısa operasyon özeti.">
            <div className="stack">
              <p className="muted">
                Liste, gerçekleşmeme riski yüksek rezervasyonları önce aramak için hazırlanır. Teknik model metrikleri
                ekip içi değerlendirme içindir; günlük kullanımda arama havuzu ve kanal kırılımları takip edilir.
              </p>
            </div>
          </PanelCard>

          <PanelCard title="İlk Liste" subtitle="Sınırlı ekip zamanı varsa üst sıra izlenir.">
            <div className="summary-band">
              <div className="summary-cell">
                İlk 50 kayıt
                <strong>{top50 ? `${top50.captured_no_show} sorunlu` : "-"}</strong>
              </div>
              <div className="summary-cell">
                Yakalama oranı
                <strong>{top50 ? `${(top50.recall * 100).toFixed(1)}%` : "-"}</strong>
              </div>
            </div>
          </PanelCard>
        </div>

        <div className="grid-two">
          <PanelCard
            title="Havuz Boyutu Senaryoları"
            subtitle="Daha düşük sınır daha büyük arama listesi üretir."
          >
            {recommendedThresholdRows.length === 0 ? (
              <div className="empty-state">Henüz takip sınırı özeti yok.</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Kesim</th>
                    <th>Aranacak kayıt</th>
                    <th>Beklenen isabet</th>
                    <th>Yakalama</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendedThresholdRows.map((row) => (
                    <tr key={`${recommendedModel}-${row.threshold}`}>
                      <td className="table-score">{row.threshold.toFixed(2)}</td>
                      <td className="table-score">{row.actioned_count}</td>
                      <td className="table-score">{row.precision.toFixed(3)}</td>
                      <td className="table-score">{row.recall.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </PanelCard>

          <PanelCard
            title="Sabit Liste Senaryoları"
            subtitle="Ekip yalnızca ilk 50, 100 veya belirli yüzdeyi arayacaksa beklenen yakalama."
          >
            {recommendedTopKRows.length === 0 ? (
              <div className="empty-state">Henüz sabit liste özeti yok.</div>
            ) : (
              <div className="stack">
                <CaptureBarChart rows={recommendedTopKRows} />
                <table className="table">
                  <thead>
                    <tr>
                      <th>Dilim</th>
                      <th>Seçilen</th>
                      <th>Yakalanan sorunlu</th>
                      <th>Toplam sorunlu</th>
                      <th>Yakalama</th>
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
              </div>
            )}
          </PanelCard>
        </div>

        <PanelCard title="Teknik Ek" subtitle="Bu alan operasyon kullanımı için değil, proje değerlendirmesi içindir.">
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

import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { PanelCard } from "@/components/panel-card";
import { ReservationActionsPanel } from "@/components/reservation-actions-panel";
import { RiskBadge } from "@/components/risk-badge";
import { getReservationDetail } from "@/lib/api";
import { formatDataSourceLabel, formatPropertyLabel } from "@/lib/presentation";

type ReservationDetailPageProps = {
  params: Promise<{
    reservationId: string;
  }>;
};

export default async function ReservationDetailPage({ params }: ReservationDetailPageProps) {
  const { reservationId } = await params;
  const detail = await getReservationDetail(reservationId);
  const latestPrediction = detail.latest_prediction;

  return (
    <AppShell currentRoute="/reservations">
      <div className="page-grid">
        <PageHeader
          title={`Rezervasyon #${detail.reservation_id || reservationId}`}
          description="Son skor, yönlendirme bağlamı ve operasyon için gereken temel alanların yer aldığı detay görünümü."
          badges={[
            formatPropertyLabel(detail.property_id),
            detail.distribution_channel ?? "Kanal bilinmiyor",
            formatDataSourceLabel(detail.data_source),
          ]}
        />

        <div className="section-note">
          <Link className="table-link" href="/reservations">
            Rezervasyon listesine dön
          </Link>
          <span className="pill">
            Aksiyon akışı: {detail.action_support_enabled ? "Yazılabilir" : "Read-only"}
          </span>
        </div>

        <section className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Son skor</div>
            <div className="metric-value">{latestPrediction?.score?.toFixed(3) ?? "-"}</div>
            <div className="muted">{latestPrediction?.scored_at ?? "Henüz skorlanmadı"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Risk seviyesi</div>
            <div className="metric-value">
              <RiskBadge riskClass={latestPrediction?.risk_class ?? null} />
            </div>
            <div className="muted">{detail.distribution_channel ?? "Kanal bilgisi yok"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Giriş tarihi</div>
            <div className="metric-value">{detail.arrival_date ?? "-"}</div>
            <div className="muted">{detail.customer_type ?? "Müşteri tipi bilinmiyor"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Gerçekleşen sonuç</div>
            <div className="metric-value">
              {detail.no_show_flag === null ? "Bilinmiyor" : detail.no_show_flag ? "Gelmedi" : "Konakladı"}
            </div>
            <div className="muted">
              {detail.excluded_from_training
                ? detail.exclusion_reason ?? "Eğitim verisine alınmadı"
                : "Değerlendirme setine dahil edildi"}
            </div>
          </div>
        </section>

        <PanelCard title="Rezervasyon Bağlamı" subtitle="Gereksiz ham alanları göstermeden sade tutuldu.">
          <div className="kv-grid">
            <div className="kv-card">
              <div className="kv-label">Otel</div>
              <div className="kv-value">{formatPropertyLabel(detail.property_id)}</div>
            </div>
            <div className="kv-card">
              <div className="kv-label">Rezervasyona kalan gün</div>
              <div className="kv-value">{detail.lead_time_days ?? "-"}</div>
            </div>
            <div className="kv-card">
              <div className="kv-label">Rezervasyon kanalı</div>
              <div className="kv-value">{detail.distribution_channel ?? "-"}</div>
            </div>
            <div className="kv-card">
              <div className="kv-label">Pazar segmenti</div>
              <div className="kv-value">{detail.market_segment ?? "-"}</div>
            </div>
            <div className="kv-card">
              <div className="kv-label">Ön ödeme tipi</div>
              <div className="kv-value">{detail.deposit_type ?? "-"}</div>
            </div>
            <div className="kv-card">
              <div className="kv-label">Ayrılan oda tipi</div>
              <div className="kv-value">{detail.reserved_room_type ?? "-"}</div>
            </div>
          </div>
        </PanelCard>

        <div className="grid-two">
          <PanelCard title="Operasyon İpuçları" subtitle="Temiz rezervasyon katmanından gelen güvenli bağlamsal alanlar.">
            <div className="kv-grid">
              <div className="kv-card">
                <div className="kv-label">Pansiyon tipi</div>
                <div className="kv-value">{detail.context?.meal_plan ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Tekrarlayan misafir</div>
                <div className="kv-value">
                  {detail.context?.is_repeated_guest === null
                    ? "-"
                    : detail.context?.is_repeated_guest
                      ? "Evet"
                      : "Hayır"}
                </div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Özel istek sayısı</div>
                <div className="kv-value">{detail.context?.total_special_requests ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Otopark talebi</div>
                <div className="kv-value">{detail.context?.required_car_parking_spaces ?? "-"}</div>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Skorlama Özeti" subtitle="Yalnızca son skor kaydına ait operasyonel metaveri gösterilir.">
            <div className="kv-grid">
              <div className="kv-card">
                <div className="kv-label">Skor zamanı</div>
                <div className="kv-value">{latestPrediction?.scored_at ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Skor</div>
                <div className="kv-value">{latestPrediction?.score?.toFixed(3) ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Risk etiketi</div>
                <div className="kv-value">{latestPrediction?.risk_class ? <RiskBadge riskClass={latestPrediction.risk_class} /> : "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Kaynak dosya</div>
                <div className="kv-value">{detail.source_file}</div>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="Aksiyon Geçmişi" subtitle="Manuel müdahale, takip ve kapanış akışı bu panelde tutulur.">
          <ReservationActionsPanel
            reservationId={detail.reservation_id}
            actionSupportEnabled={detail.action_support_enabled}
            initialActions={detail.actions}
          />
        </PanelCard>
      </div>
    </AppShell>
  );
}

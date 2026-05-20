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
          description="Misafiri aramadan önce kontrol edilecek temel bilgiler ve önerilen takip adımı."
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
            Takip kaydı: {detail.action_support_enabled ? "Açık" : "Sadece görüntüleme"}
          </span>
        </div>

        <section className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Öncelik puanı</div>
            <div className="metric-value">{latestPrediction?.score?.toFixed(3) ?? "-"}</div>
            <div className="muted">{latestPrediction?.scored_at ?? "Henüz listeye alınmadı"}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Takip önceliği</div>
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
            <div className="metric-label">Sonuç</div>
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

        <PanelCard title="Arama Öncesi Kontrol" subtitle="Misafire ulaşmadan önce görülecek kısa özet.">
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
          <PanelCard title="Önerilen Takip" subtitle="Bu kayıt için ilk temas önerisi.">
            <div className="call-script">
              <div>
                <span className="tag">1</span>
                <strong>Varış teyidi al</strong>
                <p className="muted">Misafirin giriş tarihini ve tahmini varış saatini doğrula.</p>
              </div>
              <div>
                <span className="tag">2</span>
                <strong>Garanti durumunu kontrol et</strong>
                <p className="muted">Depozito, ödeme tipi veya acente garantisi eksikse not düş.</p>
              </div>
              <div>
                <span className="tag">3</span>
                <strong>Sonraki adımı kaydet</strong>
                <p className="muted">Ulaşıldı, mesaj gönderildi veya tekrar aranacak bilgisini takip kaydı olarak ekle.</p>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Operasyon İpuçları" subtitle="Konuşma sırasında yardımcı olacak kısa bilgiler.">
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

          <PanelCard title="Liste Bilgisi" subtitle="Kayıt hangi öncelikle kuyruğa alındı?">
            <div className="kv-grid">
              <div className="kv-card">
                <div className="kv-label">Listeye alınma zamanı</div>
                <div className="kv-value">{latestPrediction?.scored_at ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Öncelik puanı</div>
                <div className="kv-value">{latestPrediction?.score?.toFixed(3) ?? "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Takip etiketi</div>
                <div className="kv-value">{latestPrediction?.risk_class ? <RiskBadge riskClass={latestPrediction.risk_class} /> : "-"}</div>
              </div>
              <div className="kv-card">
                <div className="kv-label">Kaynak dosya</div>
                <div className="kv-value">{detail.source_file}</div>
              </div>
            </div>
          </PanelCard>
        </div>

        <PanelCard title="Takip Geçmişi" subtitle="Arama, mesaj, garanti kontrolü ve kapanış bilgisi bu panelde tutulur.">
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

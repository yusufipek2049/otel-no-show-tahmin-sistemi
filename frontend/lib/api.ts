import type {
  BenchmarkReport,
  DashboardSummary,
  ReservationDetail,
  ReservationListResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const dashboardFallback: DashboardSummary = {
  kpis: {
    total_reservations: 0,
    high_risk_reservations: 0,
    medium_risk_reservations: 0,
    latest_scored_at: null,
    active_model_name: null,
    active_model_version: null,
  },
  items: [],
};

const reservationsFallback: ReservationListResponse = {
  total: 0,
  items: [],
  filters: {
    property_ids: [],
    distribution_channels: [],
    risk_classes: ["high", "medium", "low"],
    min_arrival_date: null,
    max_arrival_date: null,
    model_name: null,
    model_version: null,
  },
};

const reservationDetailFallback: ReservationDetail = {
  reservation_id: 0,
  property_id: "Unavailable",
  source_file: "Hazır değil",
  arrival_date: null,
  lead_time_days: null,
  distribution_channel: null,
  market_segment: null,
  customer_type: null,
  reserved_room_type: null,
  deposit_type: null,
  no_show_flag: null,
  excluded_from_training: false,
  exclusion_reason: null,
  latest_prediction: null,
  context: null,
};

const reportFallback: BenchmarkReport = {
  split_strategy: "Zaman bazlı bölme planlandı: erken dönemlerde eğitim, daha sonraki dönemde doğrulama.",
  primary_metrics: ["pr_auc", "roc_auc", "precision", "recall", "f1", "calibration"],
  recommended_model: null,
  selected_threshold: null,
  recommendation_reason: null,
  models: [
    {
      model_name: "logistic_regression",
      status: "planned",
      notes: "İlk iskelet hazır. Eğitim hattı tamamlandığında değerlendirme metrikleri burada görünecek.",
      metrics: [
        { name: "pr_auc", value: null, status: "pending" },
        { name: "roc_auc", value: null, status: "pending" },
      ],
    },
    {
      model_name: "catboost",
      status: "planned",
      notes: "Veri aktarımı ve leakage güvenli özellik seti tamamlandığında öne çıkan tablo adayı.",
      metrics: [
        { name: "pr_auc", value: null, status: "pending" },
        { name: "roc_auc", value: null, status: "pending" },
      ],
    },
  ],
  comparison: [],
  threshold_tables: {},
  top_k_tables: {},
};

async function safeFetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      next: { revalidate: 0 },
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return fallback;
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return safeFetchJson("/dashboard/summary", dashboardFallback);
}

export async function getReservations(filters?: Record<string, string | undefined>): Promise<ReservationListResponse> {
  const params = new URLSearchParams();

  Object.entries(filters ?? {}).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });

  const queryString = params.toString();
  const query = queryString ? `?${queryString}` : "";
  return safeFetchJson(`/reservations${query}`, reservationsFallback);
}

export async function getReservationDetail(reservationId: string | number): Promise<ReservationDetail> {
  return safeFetchJson(`/reservations/${reservationId}`, reservationDetailFallback);
}

export async function getBenchmarkReport(): Promise<BenchmarkReport> {
  return safeFetchJson("/reports/benchmark", reportFallback);
}

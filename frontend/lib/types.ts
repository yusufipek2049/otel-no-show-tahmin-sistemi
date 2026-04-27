export type DashboardSummary = {
  kpis: {
    total_reservations: number;
    high_risk_reservations: number;
    medium_risk_reservations: number;
    action_pending_count: number;
    action_completed_count: number;
    action_follow_up_count: number;
    latest_scored_at: string | null;
    active_model_name: string | null;
    active_model_version: string | null;
  };
  items: ReservationListItem[];
  data_source: string;
  scoring_status: string;
  action_support_enabled: boolean;
};

export type ReservationListItem = {
  reservation_id: number;
  property_id: string;
  source_file?: string;
  arrival_date: string | null;
  distribution_channel: string | null;
  customer_type?: string | null;
  no_show_flag?: boolean | null;
  score: number | null;
  risk_class: string | null;
  model_name?: string | null;
  model_version?: string | null;
  scored_at?: string | null;
};

export type ReservationFilterOptions = {
  property_ids: string[];
  distribution_channels: string[];
  risk_classes: string[];
  min_arrival_date: string | null;
  max_arrival_date: string | null;
  model_name: string | null;
  model_version: string | null;
};

export type ReservationListResponse = {
  total: number;
  items: ReservationListItem[];
  filters: ReservationFilterOptions;
};

export type ReservationDetail = {
  reservation_id: number;
  property_id: string;
  source_file: string;
  arrival_date: string | null;
  lead_time_days: number | null;
  distribution_channel: string | null;
  market_segment: string | null;
  customer_type: string | null;
  reserved_room_type: string | null;
  deposit_type: string | null;
  no_show_flag: boolean | null;
  excluded_from_training: boolean;
  exclusion_reason: string | null;
  latest_prediction: ReservationListItem | null;
  actions: ReservationAction[];
  context: {
    meal_plan: string | null;
    is_repeated_guest: boolean | null;
    total_special_requests: number | null;
    required_car_parking_spaces: number | null;
  } | null;
  data_source: string;
  action_support_enabled: boolean;
};

export type ReservationAction = {
  id: number;
  reservation_id: number;
  prediction_id: number | null;
  action_type: string;
  action_status: string;
  action_note: string | null;
  acted_by: string;
  payload: Record<string, unknown>;
  acted_at: string;
};

export type BenchmarkReport = {
  split_strategy: string;
  primary_metrics: string[];
  recommended_model: string | null;
  selected_threshold: number | null;
  recommendation_reason: string | null;
  models: Array<{
    model_name: string;
    status: string;
    notes: string;
    metrics: Array<{
      name: string;
      value: number | null;
      status: string;
    }>;
  }>;
  comparison: Array<{
    model_name: string;
    model_version: string;
    roc_auc: number | null;
    pr_auc: number | null;
    precision: number | null;
    recall: number | null;
    f1: number | null;
    brier_score: number | null;
    threshold: number | null;
  }>;
  threshold_tables: Record<
    string,
    Array<{
      threshold: number;
      precision: number;
      recall: number;
      f1: number;
      actioned_count: number;
    }>
  >;
  top_k_tables: Record<
    string,
    Array<{
      segment: string;
      selected_count: number;
      captured_no_show: number;
      total_no_show: number;
      recall: number;
    }>
  >;
};

export type OperationsSummary = {
  total_reservations: number;
  scored_reservations: number;
  no_show_count: number;
  canceled_count: number;
  no_show_rate: number;
  cancellation_rate: number;
  high_risk_reservations: number;
  action_pending_count: number;
  action_completed_count: number;
  action_follow_up_count: number;
  data_source: string;
  action_support_enabled: boolean;
  note: string | null;
};

export type TrendPoint = {
  period: string;
  total_reservations: number;
  no_show_count: number;
  canceled_count: number;
  no_show_rate: number;
  cancellation_rate: number;
};

export type DimensionBreakdownRow = {
  dimension_value: string;
  total_reservations: number;
  scored_reservations: number;
  high_risk_reservations: number;
  no_show_count: number;
  canceled_count: number;
  no_show_rate: number;
  cancellation_rate: number;
  average_score: number | null;
};

export type ActionEffectiveness = {
  total_actions: number;
  open_actions: number;
  completed_actions: number;
  follow_up_actions: number;
  high_risk_with_action_count: number;
  high_risk_without_action_count: number;
  status_breakdown: Array<{
    label: string;
    count: number;
  }>;
  type_breakdown: Array<{
    label: string;
    count: number;
  }>;
  data_source: string;
  action_support_enabled: boolean;
  note: string | null;
};

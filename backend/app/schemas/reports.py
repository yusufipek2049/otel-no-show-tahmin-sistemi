from __future__ import annotations

from pydantic import BaseModel


class BenchmarkMetric(BaseModel):
    name: str
    value: float | None = None
    status: str


class BenchmarkModelStatus(BaseModel):
    model_name: str
    status: str
    notes: str
    metrics: list[BenchmarkMetric]


class BenchmarkComparisonRow(BaseModel):
    model_name: str
    model_version: str
    roc_auc: float | None = None
    pr_auc: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    brier_score: float | None = None
    threshold: float | None = None


class ThresholdMetricRow(BaseModel):
    threshold: float
    precision: float
    recall: float
    f1: float
    actioned_count: int


class TopKMetricRow(BaseModel):
    segment: str
    selected_count: int
    captured_no_show: int
    total_no_show: int
    recall: float


class BenchmarkReportResponse(BaseModel):
    split_strategy: str
    primary_metrics: list[str]
    recommended_model: str | None = None
    selected_threshold: float | None = None
    recommendation_reason: str | None = None
    models: list[BenchmarkModelStatus]
    comparison: list[BenchmarkComparisonRow] = []
    threshold_tables: dict[str, list[ThresholdMetricRow]] = {}
    top_k_tables: dict[str, list[TopKMetricRow]] = {}


class OperationsSummaryResponse(BaseModel):
    total_reservations: int
    scored_reservations: int
    no_show_count: int
    canceled_count: int
    no_show_rate: float
    cancellation_rate: float
    high_risk_reservations: int
    action_pending_count: int
    action_completed_count: int
    action_follow_up_count: int
    data_source: str
    action_support_enabled: bool
    note: str | None = None


class TrendPoint(BaseModel):
    period: str
    total_reservations: int
    no_show_count: int
    canceled_count: int
    no_show_rate: float
    cancellation_rate: float


class DimensionBreakdownRow(BaseModel):
    dimension_value: str
    total_reservations: int
    scored_reservations: int
    high_risk_reservations: int
    no_show_count: int
    canceled_count: int
    no_show_rate: float
    cancellation_rate: float
    average_score: float | None = None


class ActionBreakdownRow(BaseModel):
    label: str
    count: int


class ActionEffectivenessResponse(BaseModel):
    total_actions: int
    open_actions: int
    completed_actions: int
    follow_up_actions: int
    high_risk_with_action_count: int
    high_risk_without_action_count: int
    status_breakdown: list[ActionBreakdownRow]
    type_breakdown: list[ActionBreakdownRow]
    data_source: str
    action_support_enabled: bool
    note: str | None = None

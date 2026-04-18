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

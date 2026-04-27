from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.reports import ReportsRepository
from app.schemas.reports import (
    ActionEffectivenessResponse,
    BenchmarkReportResponse,
    DimensionBreakdownRow,
    OperationsSummaryResponse,
    TrendPoint,
)


class ReportsService:
    def __init__(self, db: Session) -> None:
        self.repository = ReportsRepository(db)
        self.artifact_repository = ArtifactViewRepository()

    def _reporting_source(self) -> tuple[str, bool]:
        try:
            if self.repository.has_prediction_data():
                return "database_prediction_store", True
        except SQLAlchemyError:
            pass

        if self.artifact_repository.exists():
            return "artifact_fallback", False

        return "database_bootstrap", False

    def get_benchmark_report(self) -> BenchmarkReportResponse:
        if self.artifact_repository.exists():
            return BenchmarkReportResponse.model_validate(self.artifact_repository.get_benchmark_report())
        return BenchmarkReportResponse.model_validate(self.repository.get_bootstrap_benchmark_report())

    def get_operations_summary(self) -> OperationsSummaryResponse:
        data_source, action_support_enabled = self._reporting_source()
        if data_source == "artifact_fallback":
            payload = self.artifact_repository.get_operations_summary()
        elif data_source == "database_prediction_store":
            payload = self.repository.get_operations_summary()
        else:
            payload = {
                "total_reservations": 0,
                "scored_reservations": 0,
                "no_show_count": 0,
                "canceled_count": 0,
                "no_show_rate": 0.0,
                "cancellation_rate": 0.0,
                "high_risk_reservations": 0,
                "action_pending_count": 0,
                "action_completed_count": 0,
                "action_follow_up_count": 0,
                "note": "Prediction store is not ready yet.",
            }

        payload["data_source"] = data_source
        payload["action_support_enabled"] = action_support_enabled
        return OperationsSummaryResponse.model_validate(payload)

    def get_no_show_trends(self) -> list[TrendPoint]:
        data_source, _ = self._reporting_source()
        if data_source == "artifact_fallback":
            rows = self.artifact_repository.get_no_show_trends()
        elif data_source == "database_prediction_store":
            rows = self.repository.get_no_show_trends()
        else:
            rows = []
        return [TrendPoint.model_validate(row) for row in rows]

    def get_channel_breakdown(self) -> list[DimensionBreakdownRow]:
        data_source, _ = self._reporting_source()
        if data_source == "artifact_fallback":
            rows = self.artifact_repository.get_dimension_breakdown("distribution_channel")
        elif data_source == "database_prediction_store":
            rows = self.repository.get_dimension_breakdown("distribution_channel")
        else:
            rows = []
        return [DimensionBreakdownRow.model_validate(row) for row in rows]

    def get_segment_breakdown(self) -> list[DimensionBreakdownRow]:
        data_source, _ = self._reporting_source()
        if data_source == "artifact_fallback":
            rows = self.artifact_repository.get_dimension_breakdown("market_segment")
        elif data_source == "database_prediction_store":
            rows = self.repository.get_dimension_breakdown("market_segment")
        else:
            rows = []
        return [DimensionBreakdownRow.model_validate(row) for row in rows]

    def get_action_effectiveness(self) -> ActionEffectivenessResponse:
        data_source, action_support_enabled = self._reporting_source()
        if data_source == "artifact_fallback":
            payload = self.artifact_repository.get_action_effectiveness()
        elif data_source == "database_prediction_store":
            payload = self.repository.get_action_effectiveness()
        else:
            payload = {
                "total_actions": 0,
                "open_actions": 0,
                "completed_actions": 0,
                "follow_up_actions": 0,
                "high_risk_with_action_count": 0,
                "high_risk_without_action_count": 0,
                "status_breakdown": [],
                "type_breakdown": [],
                "note": "Action analytics become available after prediction persistence and action logging.",
            }

        payload["data_source"] = data_source
        payload["action_support_enabled"] = action_support_enabled
        return ActionEffectivenessResponse.model_validate(payload)

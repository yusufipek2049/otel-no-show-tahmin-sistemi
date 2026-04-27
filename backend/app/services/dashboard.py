from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.dashboard import DashboardRepository
from app.repositories.reservations import prediction_store_has_rows
from app.schemas.dashboard import DashboardKpis, DashboardSummaryResponse


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repository = DashboardRepository(db)
        self.artifact_repository = ArtifactViewRepository()

    def _resolve_source(self) -> tuple[str, str, bool]:
        try:
            if prediction_store_has_rows(self.repository.db):
                return "database_prediction_store", "ready", True
        except SQLAlchemyError:
            pass

        if self.artifact_repository.exists():
            return "artifact_fallback", "artifact_fallback", False

        return "database_bootstrap", "awaiting_predictions", False

    def get_summary(self) -> DashboardSummaryResponse:
        data_source, scoring_status, action_support_enabled = self._resolve_source()
        if data_source == "artifact_fallback":
            payload = self.artifact_repository.get_dashboard_summary()
            payload["data_source"] = data_source
            payload["scoring_status"] = scoring_status
            payload["action_support_enabled"] = action_support_enabled
            return DashboardSummaryResponse.model_validate(payload)

        try:
            return DashboardSummaryResponse(
                kpis=self.repository.get_kpis(),
                items=self.repository.get_recent_risky_reservations(),
                data_source=data_source,
                scoring_status=scoring_status,
                action_support_enabled=action_support_enabled,
            )
        except SQLAlchemyError:
            return DashboardSummaryResponse(
                kpis=DashboardKpis(
                    total_reservations=0,
                    high_risk_reservations=0,
                    medium_risk_reservations=0,
                    action_pending_count=0,
                    action_completed_count=0,
                    action_follow_up_count=0,
                    latest_scored_at=None,
                    active_model_name=None,
                    active_model_version=None,
                ),
                items=[],
                data_source="database_bootstrap",
                scoring_status="awaiting_predictions",
                action_support_enabled=False,
            )

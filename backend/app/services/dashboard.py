from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.dashboard import DashboardRepository
from app.repositories.reservations import prediction_store_has_rows
from app.schemas.dashboard import DashboardKpis, DashboardSummaryResponse
from app.core.logging import get_logger, log_event
from app.training.constants import DEFAULT_ARTIFACTS_ROOT
from app.training.stages import ModelStage

logger = get_logger(__name__)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repository = DashboardRepository(db)
        self.artifact_repository = ArtifactViewRepository(
            DEFAULT_ARTIFACTS_ROOT / ModelStage.ARRIVAL_FAILURE_POST_BOOKING.value / "latest"
        )

    def _resolve_source(self) -> tuple[str, str, bool]:
        try:
            if prediction_store_has_rows(self.repository.db):
                source = ("database_prediction_store", "ready", True)
                logger.info(log_event("scoring_source_resolved", source=source[0], action_support_enabled=source[2]))
                return source
        except SQLAlchemyError:
            logger.warning(log_event("scoring_source_resolution_failed", source="database_prediction_store"))

        if self.artifact_repository.exists():
            source = ("artifact_fallback", "artifact_fallback", False)
            logger.info(log_event("scoring_source_resolved", source=source[0], action_support_enabled=source[2]))
            return source

        source = ("database_bootstrap", "awaiting_predictions", False)
        logger.info(log_event("scoring_source_resolved", source=source[0], action_support_enabled=source[2]))
        return source

    def get_summary(self) -> DashboardSummaryResponse:
        data_source, scoring_status, action_support_enabled = self._resolve_source()
        if data_source == "artifact_fallback":
            payload = self.artifact_repository.get_dashboard_summary()
            payload["data_source"] = data_source
            payload["scoring_status"] = scoring_status
            payload["action_support_enabled"] = action_support_enabled
            return DashboardSummaryResponse.model_validate(payload)

        try:
            return DashboardSummaryResponse.model_validate(
                {
                    "kpis": self.repository.get_kpis(),
                    "items": self.repository.get_recent_risky_reservations(),
                    "data_source": data_source,
                    "scoring_status": scoring_status,
                    "action_support_enabled": action_support_enabled,
                }
            )
        except SQLAlchemyError:
            logger.warning(log_event("dashboard_summary_database_unavailable", fallback="database_bootstrap"))
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

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import DashboardKpis, DashboardSummaryResponse


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repository = DashboardRepository(db)
        self.artifact_repository = ArtifactViewRepository()

    def get_summary(self) -> DashboardSummaryResponse:
        if self.artifact_repository.exists():
            return DashboardSummaryResponse.model_validate(self.artifact_repository.get_dashboard_summary())

        try:
            return DashboardSummaryResponse(
                kpis=self.repository.get_kpis(),
                items=self.repository.get_recent_risky_reservations(),
            )
        except SQLAlchemyError:
            return DashboardSummaryResponse(
                kpis=DashboardKpis(
                    total_reservations=0,
                    high_risk_reservations=0,
                    medium_risk_reservations=0,
                    latest_scored_at=None,
                    active_model_name=None,
                    active_model_version=None,
                ),
                items=[],
            )

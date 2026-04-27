from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import ReservationAction
from app.models.prediction import Prediction
from app.models.reservation import ReservationClean
from app.repositories.reservations import build_latest_prediction_subquery


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.latest_predictions = build_latest_prediction_subquery()

    def get_kpis(self) -> dict[str, object]:
        total_reservations = self.db.scalar(select(func.count()).select_from(ReservationClean)) or 0
        high_risk = (
            self.db.scalar(
                select(func.count())
                .select_from(self.latest_predictions)
                .where(self.latest_predictions.c.risk_class == "high")
            )
            or 0
        )
        medium_risk = (
            self.db.scalar(
                select(func.count())
                .select_from(self.latest_predictions)
                .where(self.latest_predictions.c.risk_class == "medium")
            )
            or 0
        )
        latest_scored_at = self.db.scalar(select(func.max(Prediction.scored_at)))
        action_pending_count = (
            self.db.scalar(
                select(func.count())
                .select_from(ReservationAction)
                .where(ReservationAction.action_status == "open")
            )
            or 0
        )
        action_completed_count = (
            self.db.scalar(
                select(func.count())
                .select_from(ReservationAction)
                .where(ReservationAction.action_status == "completed")
            )
            or 0
        )
        action_follow_up_count = (
            self.db.scalar(
                select(func.count())
                .select_from(ReservationAction)
                .where(ReservationAction.action_status == "follow_up")
            )
            or 0
        )

        return {
            "total_reservations": total_reservations,
            "high_risk_reservations": high_risk,
            "medium_risk_reservations": medium_risk,
            "action_pending_count": action_pending_count,
            "action_completed_count": action_completed_count,
            "action_follow_up_count": action_follow_up_count,
            "latest_scored_at": latest_scored_at,
        }

    def get_recent_risky_reservations(self, limit: int = 8) -> list[dict[str, object]]:
        stmt = (
            select(
                ReservationClean.id.label("reservation_id"),
                ReservationClean.property_id.label("property_id"),
                ReservationClean.arrival_date.label("arrival_date"),
                ReservationClean.distribution_channel.label("distribution_channel"),
                self.latest_predictions.c.risk_class.label("risk_class"),
                self.latest_predictions.c.score.label("score"),
                self.latest_predictions.c.model_version.label("model_version"),
            )
            .select_from(ReservationClean)
            .join(
                self.latest_predictions,
                self.latest_predictions.c.reservation_clean_id == ReservationClean.id,
            )
            .order_by(self.latest_predictions.c.score.desc(), ReservationClean.id.desc())
            .limit(limit)
        )
        return [dict(row) for row in self.db.execute(stmt).mappings().all()]

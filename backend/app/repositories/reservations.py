from __future__ import annotations

from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.reservation import ReservationClean


def build_latest_prediction_subquery():
    ranked_predictions = (
        select(
            Prediction.id.label("prediction_id"),
            Prediction.reservation_clean_id.label("reservation_clean_id"),
            Prediction.model_name.label("model_name"),
            Prediction.model_version.label("model_version"),
            Prediction.score.label("score"),
            Prediction.risk_class.label("risk_class"),
            Prediction.threshold_used.label("threshold_used"),
            Prediction.scored_at.label("scored_at"),
            func.row_number()
            .over(
                partition_by=Prediction.reservation_clean_id,
                order_by=(Prediction.scored_at.desc(), Prediction.id.desc()),
            )
            .label("prediction_rank"),
        )
        .subquery()
    )

    return select(ranked_predictions).where(ranked_predictions.c.prediction_rank == 1).subquery()


def apply_reservation_filters(
    stmt: Select,
    *,
    property_id: str | None = None,
    distribution_channel: str | None = None,
    risk_class: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Select:
    if property_id:
        stmt = stmt.where(ReservationClean.property_id == property_id)
    if distribution_channel:
        stmt = stmt.where(ReservationClean.distribution_channel == distribution_channel)
    if date_from:
        stmt = stmt.where(ReservationClean.arrival_date >= date_from)
    if date_to:
        stmt = stmt.where(ReservationClean.arrival_date <= date_to)
    return stmt


class ReservationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.latest_predictions = build_latest_prediction_subquery()

    def list_reservations(
        self,
        *,
        property_id: str | None = None,
        distribution_channel: str | None = None,
        risk_class: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
    ) -> tuple[int, list[dict[str, object]]]:
        base_stmt = (
            select(
                ReservationClean.id.label("reservation_id"),
                ReservationClean.property_id.label("property_id"),
                ReservationClean.source_file.label("source_file"),
                ReservationClean.arrival_date.label("arrival_date"),
                ReservationClean.distribution_channel.label("distribution_channel"),
                ReservationClean.customer_type.label("customer_type"),
                ReservationClean.no_show_flag.label("no_show_flag"),
                self.latest_predictions.c.score.label("score"),
                self.latest_predictions.c.risk_class.label("risk_class"),
                self.latest_predictions.c.model_name.label("model_name"),
                self.latest_predictions.c.model_version.label("model_version"),
                self.latest_predictions.c.scored_at.label("scored_at"),
            )
            .select_from(ReservationClean)
            .outerjoin(
                self.latest_predictions,
                self.latest_predictions.c.reservation_clean_id == ReservationClean.id,
            )
        )

        base_stmt = apply_reservation_filters(
            base_stmt,
            property_id=property_id,
            distribution_channel=distribution_channel,
            risk_class=risk_class,
            date_from=date_from,
            date_to=date_to,
        )

        if risk_class:
            base_stmt = base_stmt.where(self.latest_predictions.c.risk_class == risk_class)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        items_stmt = (
            base_stmt.order_by(
                self.latest_predictions.c.score.desc().nullslast(),
                ReservationClean.arrival_date.desc().nullslast(),
                ReservationClean.id.desc(),
            )
            .limit(limit)
        )

        items = self.db.execute(items_stmt).mappings().all()
        return total, [dict(item) for item in items]

    def get_reservation_detail(self, reservation_id: int) -> dict[str, object] | None:
        stmt = (
            select(
                ReservationClean.id.label("reservation_id"),
                ReservationClean.property_id.label("property_id"),
                ReservationClean.source_file.label("source_file"),
                ReservationClean.arrival_date.label("arrival_date"),
                ReservationClean.lead_time_days.label("lead_time_days"),
                ReservationClean.distribution_channel.label("distribution_channel"),
                ReservationClean.market_segment.label("market_segment"),
                ReservationClean.customer_type.label("customer_type"),
                ReservationClean.reserved_room_type.label("reserved_room_type"),
                ReservationClean.deposit_type.label("deposit_type"),
                ReservationClean.no_show_flag.label("no_show_flag"),
                ReservationClean.excluded_from_training.label("excluded_from_training"),
                ReservationClean.exclusion_reason.label("exclusion_reason"),
                self.latest_predictions.c.score.label("score"),
                self.latest_predictions.c.risk_class.label("risk_class"),
                self.latest_predictions.c.model_name.label("model_name"),
                self.latest_predictions.c.model_version.label("model_version"),
                self.latest_predictions.c.scored_at.label("scored_at"),
            )
            .select_from(ReservationClean)
            .outerjoin(
                self.latest_predictions,
                self.latest_predictions.c.reservation_clean_id == ReservationClean.id,
            )
            .where(ReservationClean.id == reservation_id)
        )
        row = self.db.execute(stmt).mappings().first()
        return dict(row) if row else None

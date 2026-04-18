from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.reservations import ReservationRepository
from app.schemas.reservations import (
    ReservationContext,
    ReservationDetailResponse,
    ReservationFilterOptions,
    ReservationListItem,
    ReservationListResponse,
)


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.repository = ReservationRepository(db)
        self.artifact_repository = ArtifactViewRepository()

    def list_reservations(
        self,
        *,
        property_id: str | None = None,
        distribution_channel: str | None = None,
        risk_class: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
    ) -> ReservationListResponse:
        if self.artifact_repository.exists():
            total, items, filters = self.artifact_repository.list_reservations(
                property_id=property_id,
                distribution_channel=distribution_channel,
                risk_class=risk_class,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            )
            return ReservationListResponse(
                total=total,
                items=[ReservationListItem.model_validate(item) for item in items],
                filters=ReservationFilterOptions.model_validate(filters),
            )

        try:
            total, items = self.repository.list_reservations(
                property_id=property_id,
                distribution_channel=distribution_channel,
                risk_class=risk_class,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            )
        except SQLAlchemyError:
            total, items = 0, []

        return ReservationListResponse(
            total=total,
            items=[ReservationListItem.model_validate(item) for item in items],
            filters=ReservationFilterOptions(
                property_ids=[],
                distribution_channels=[],
                risk_classes=["high", "medium", "low"],
                min_arrival_date=None,
                max_arrival_date=None,
                model_name=None,
                model_version=None,
            ),
        )

    def get_reservation_detail(self, reservation_id: int) -> ReservationDetailResponse:
        if self.artifact_repository.exists():
            detail = self.artifact_repository.get_reservation_detail(reservation_id)
            if detail is None:
                raise HTTPException(status_code=404, detail="Reservation not found")

            latest_prediction = None
            if detail.get("latest_prediction"):
                latest_prediction = ReservationListItem.model_validate(detail["latest_prediction"])

            return ReservationDetailResponse(
                reservation_id=detail["reservation_id"],
                property_id=detail["property_id"],
                source_file=detail["source_file"],
                arrival_date=detail["arrival_date"],
                lead_time_days=detail["lead_time_days"],
                distribution_channel=detail["distribution_channel"],
                market_segment=detail["market_segment"],
                customer_type=detail["customer_type"],
                reserved_room_type=detail["reserved_room_type"],
                deposit_type=detail["deposit_type"],
                no_show_flag=detail["no_show_flag"],
                excluded_from_training=detail["excluded_from_training"],
                exclusion_reason=detail["exclusion_reason"],
                latest_prediction=latest_prediction,
                context=ReservationContext.model_validate(detail["context"]) if detail.get("context") else None,
            )

        try:
            detail = self.repository.get_reservation_detail(reservation_id)
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database is not available yet") from exc

        if detail is None:
            raise HTTPException(status_code=404, detail="Reservation not found")

        latest_prediction = None
        if detail.get("model_name") or detail.get("score") is not None:
            latest_prediction = ReservationListItem.model_validate(
                {
                    "reservation_id": detail["reservation_id"],
                    "property_id": detail["property_id"],
                    "source_file": detail["source_file"],
                    "arrival_date": detail["arrival_date"],
                    "distribution_channel": detail["distribution_channel"],
                    "customer_type": detail["customer_type"],
                    "no_show_flag": detail["no_show_flag"],
                    "score": detail["score"],
                    "risk_class": detail["risk_class"],
                    "model_name": detail["model_name"],
                    "model_version": detail["model_version"],
                    "scored_at": detail["scored_at"],
                }
            )

        return ReservationDetailResponse(
            reservation_id=detail["reservation_id"],
            property_id=detail["property_id"],
            source_file=detail["source_file"],
            arrival_date=detail["arrival_date"],
            lead_time_days=detail["lead_time_days"],
            distribution_channel=detail["distribution_channel"],
            market_segment=detail["market_segment"],
            customer_type=detail["customer_type"],
            reserved_room_type=detail["reserved_room_type"],
            deposit_type=detail["deposit_type"],
            no_show_flag=detail["no_show_flag"],
            excluded_from_training=detail["excluded_from_training"],
            exclusion_reason=detail["exclusion_reason"],
            latest_prediction=latest_prediction,
        )

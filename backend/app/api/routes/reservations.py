from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reservations import ReservationDetailResponse, ReservationListResponse
from app.services.reservations import ReservationService

router = APIRouter()


@router.get("", response_model=ReservationListResponse)
def list_reservations(
    property_id: str | None = Query(default=None),
    distribution_channel: str | None = Query(default=None),
    risk_class: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ReservationListResponse:
    return ReservationService(db).list_reservations(
        property_id=property_id,
        distribution_channel=distribution_channel,
        risk_class=risk_class,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/{reservation_id}", response_model=ReservationDetailResponse)
def get_reservation_detail(reservation_id: int, db: Session = Depends(get_db)) -> ReservationDetailResponse:
    return ReservationService(db).get_reservation_detail(reservation_id)

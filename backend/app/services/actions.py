from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.actions import ActionsRepository
from app.schemas.actions import (
    ReservationActionCreateRequest,
    ReservationActionResponse,
    ReservationActionUpdateRequest,
)


def _to_action_response(action) -> ReservationActionResponse:
    return ReservationActionResponse(
        id=action.id,
        reservation_id=action.reservation_clean_id,
        prediction_id=action.prediction_id,
        action_type=action.action_type,
        action_status=action.action_status,
        action_note=action.action_note,
        acted_by=action.acted_by,
        payload=action.payload,
        acted_at=action.acted_at,
    )


class ActionsService:
    def __init__(self, db: Session) -> None:
        self.repository = ActionsRepository(db)

    def list_reservation_actions(self, reservation_id: int) -> list[ReservationActionResponse]:
        try:
            if not self.repository.reservation_exists(reservation_id):
                raise HTTPException(status_code=404, detail="Reservation not found")
            actions = self.repository.list_reservation_actions(reservation_id)
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database is not available yet") from exc

        return [_to_action_response(action) for action in actions]

    def create_reservation_action(
        self,
        reservation_id: int,
        payload: ReservationActionCreateRequest,
    ) -> ReservationActionResponse:
        try:
            if not self.repository.reservation_exists(reservation_id):
                raise HTTPException(status_code=404, detail="Reservation not found")

            prediction_id = self.repository.get_latest_prediction_id(reservation_id)
            action = self.repository.create_action(
                reservation_id=reservation_id,
                prediction_id=prediction_id,
                action_type=payload.action_type,
                action_status=payload.action_status,
                action_note=payload.action_note,
                acted_by=payload.acted_by,
                payload=payload.payload,
            )
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database is not available yet") from exc

        return _to_action_response(action)

    def update_action(
        self,
        action_id: int,
        payload: ReservationActionUpdateRequest,
    ) -> ReservationActionResponse:
        try:
            action = self.repository.get_action(action_id)
            if action is None:
                raise HTTPException(status_code=404, detail="Action not found")

            updated = self.repository.update_action(
                action=action,
                action_status=payload.action_status,
                action_note=payload.action_note,
            )
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database is not available yet") from exc

        return _to_action_response(updated)

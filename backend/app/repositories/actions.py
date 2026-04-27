from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import ReservationAction
from app.models.reservation import ReservationClean
from app.repositories.reservations import build_latest_prediction_subquery


class ActionsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.latest_predictions = build_latest_prediction_subquery()

    def reservation_exists(self, reservation_id: int) -> bool:
        stmt = select(ReservationClean.id).where(ReservationClean.id == reservation_id)
        return self.db.scalar(stmt) is not None

    def get_action(self, action_id: int) -> ReservationAction | None:
        return self.db.get(ReservationAction, action_id)

    def get_latest_prediction_id(self, reservation_id: int) -> int | None:
        stmt = (
            select(self.latest_predictions.c.prediction_id)
            .where(self.latest_predictions.c.reservation_clean_id == reservation_id)
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_reservation_actions(self, reservation_id: int) -> list[ReservationAction]:
        stmt = (
            select(ReservationAction)
            .where(ReservationAction.reservation_clean_id == reservation_id)
            .order_by(ReservationAction.acted_at.desc(), ReservationAction.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create_action(
        self,
        *,
        reservation_id: int,
        prediction_id: int | None,
        action_type: str,
        action_status: str,
        action_note: str | None,
        acted_by: str,
        payload: dict[str, object],
    ) -> ReservationAction:
        action = ReservationAction(
            reservation_clean_id=reservation_id,
            prediction_id=prediction_id,
            action_type=action_type,
            action_status=action_status,
            action_note=action_note,
            acted_by=acted_by,
            payload=payload,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def update_action(
        self,
        *,
        action: ReservationAction,
        action_status: str | None = None,
        action_note: str | None = None,
    ) -> ReservationAction:
        if action_status is not None:
            action.action_status = action_status
        if action_note is not None:
            action.action_note = action_note

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

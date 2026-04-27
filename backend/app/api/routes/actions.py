from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.actions import ReservationActionResponse, ReservationActionUpdateRequest
from app.services.actions import ActionsService

router = APIRouter()


@router.patch("/{action_id}", response_model=ReservationActionResponse)
def update_action(
    action_id: int,
    payload: ReservationActionUpdateRequest,
    db: Session = Depends(get_db),
) -> ReservationActionResponse:
    return ActionsService(db).update_action(action_id, payload)

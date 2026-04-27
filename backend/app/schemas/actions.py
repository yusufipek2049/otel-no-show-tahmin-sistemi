from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ActionStatus = Literal["open", "completed", "follow_up"]


class ReservationActionResponse(BaseModel):
    id: int
    reservation_id: int
    prediction_id: int | None = None
    action_type: str
    action_status: ActionStatus
    action_note: str | None = None
    acted_by: str
    payload: dict[str, Any] = Field(default_factory=dict)
    acted_at: datetime


class ReservationActionCreateRequest(BaseModel):
    action_type: str = Field(min_length=2, max_length=64)
    action_status: ActionStatus = "open"
    action_note: str | None = Field(default=None, max_length=500)
    acted_by: str = Field(min_length=2, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class ReservationActionUpdateRequest(BaseModel):
    action_status: ActionStatus | None = None
    action_note: str | None = Field(default=None, max_length=500)

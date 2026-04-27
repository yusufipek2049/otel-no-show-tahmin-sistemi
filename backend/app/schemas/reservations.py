from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.actions import ReservationActionResponse


class ReservationListItem(BaseModel):
    reservation_id: int
    property_id: str
    source_file: str
    arrival_date: date | None = None
    distribution_channel: str | None = None
    customer_type: str | None = None
    no_show_flag: bool | None = None
    score: float | None = None
    risk_class: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    scored_at: datetime | None = None


class ReservationFilterOptions(BaseModel):
    property_ids: list[str]
    distribution_channels: list[str]
    risk_classes: list[str]
    min_arrival_date: date | None = None
    max_arrival_date: date | None = None
    model_name: str | None = None
    model_version: str | None = None


class ReservationListResponse(BaseModel):
    total: int
    items: list[ReservationListItem]
    filters: ReservationFilterOptions


class ReservationContext(BaseModel):
    meal_plan: str | None = None
    is_repeated_guest: bool | None = None
    total_special_requests: int | None = None
    required_car_parking_spaces: int | None = None


class ReservationDetailResponse(BaseModel):
    reservation_id: int
    property_id: str
    source_file: str
    arrival_date: date | None = None
    lead_time_days: int | None = None
    distribution_channel: str | None = None
    market_segment: str | None = None
    customer_type: str | None = None
    reserved_room_type: str | None = None
    deposit_type: str | None = None
    no_show_flag: bool | None = None
    excluded_from_training: bool
    exclusion_reason: str | None = None
    latest_prediction: ReservationListItem | None = None
    context: ReservationContext | None = None
    actions: list[ReservationActionResponse] = []
    data_source: str = "database_bootstrap"
    action_support_enabled: bool = False

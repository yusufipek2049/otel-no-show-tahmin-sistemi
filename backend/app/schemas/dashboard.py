from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_reservations: int
    high_risk_reservations: int
    medium_risk_reservations: int
    latest_scored_at: datetime | None = None
    active_model_name: str | None = None
    active_model_version: str | None = None


class DashboardReservationCard(BaseModel):
    reservation_id: int
    property_id: str
    arrival_date: date | None = None
    distribution_channel: str | None = None
    risk_class: str | None = None
    score: float | None = None
    model_version: str | None = None


class DashboardSummaryResponse(BaseModel):
    kpis: DashboardKpis
    items: list[DashboardReservationCard]

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ReservationImportBatch(TimestampMixin, Base):
    __tablename__ = "reservation_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_files: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_reservations: Mapped[list["ReservationRaw"]] = relationship(back_populates="batch")
    import_errors: Mapped[list["ReservationImportError"]] = relationship(back_populates="batch")
    clean_reservations: Mapped[list["ReservationClean"]] = relationship(back_populates="batch")


class ReservationImportError(Base):
    __tablename__ = "reservation_import_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("reservation_import_batches.id", ondelete="CASCADE"), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batch: Mapped["ReservationImportBatch"] = relationship(back_populates="import_errors")


class ReservationRaw(Base):
    __tablename__ = "reservations_raw"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_file", "source_row_number", name="uq_reservations_raw_batch_file_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("reservation_import_batches.id", ondelete="CASCADE"), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    property_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reservation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reservation_status_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batch: Mapped["ReservationImportBatch"] = relationship(back_populates="raw_reservations")
    clean_reservation: Mapped["ReservationClean | None"] = relationship(back_populates="raw_reservation", uselist=False)


class ReservationClean(TimestampMixin, Base):
    __tablename__ = "reservations_clean"
    __table_args__ = (
        Index("ix_reservations_clean_property_id", "property_id"),
        Index("ix_reservations_clean_arrival_date", "arrival_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations_raw.id", ondelete="CASCADE"), nullable=False, unique=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("reservation_import_batches.id", ondelete="CASCADE"), nullable=False)
    property_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arrival_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arrival_month_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    arrival_week_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arrival_day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekend_nights: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_nights: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adults: Mapped[int | None] = mapped_column(Integer, nullable=True)
    children: Mapped[int | None] = mapped_column(Integer, nullable=True)
    babies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meal_plan: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    market_segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    distribution_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_repeated_guest: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    previous_cancellations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_non_cancelled_bookings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reserved_room_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    deposit_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    agent_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    adr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    required_car_parking_spaces: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_special_requests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    booking_changes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_in_waiting_list: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_room_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reservation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reservation_status_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_canceled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    no_show_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    excluded_from_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    batch: Mapped["ReservationImportBatch"] = relationship(back_populates="clean_reservations")
    raw_reservation: Mapped["ReservationRaw"] = relationship(back_populates="clean_reservation")
    feature_rows: Mapped[list["ReservationFeature"]] = relationship(back_populates="reservation")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="reservation")
    actions: Mapped[list["ReservationAction"]] = relationship(back_populates="reservation")


class ReservationFeature(TimestampMixin, Base):
    __tablename__ = "reservation_features"
    __table_args__ = (
        UniqueConstraint("reservation_clean_id", "feature_set_version", name="uq_reservation_features_reservation_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_clean_id: Mapped[int] = mapped_column(ForeignKey("reservations_clean.id", ondelete="CASCADE"), nullable=False)
    feature_set_version: Mapped[str] = mapped_column(String(64), nullable=False)
    total_nights: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_guests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_children: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_family: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    lead_time_bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    has_agent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_company: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    special_request_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    adr_per_guest: Mapped[float | None] = mapped_column(Float, nullable=True)
    adr_per_night_proxy: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_high_season: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_weekend_heavy: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    previous_cancel_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    reservation: Mapped["ReservationClean"] = relationship(back_populates="feature_rows")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="feature")

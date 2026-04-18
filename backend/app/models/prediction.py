from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_reservation_clean_id", "reservation_clean_id"),
        Index("ix_predictions_model_version", "model_name", "model_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_clean_id: Mapped[int] = mapped_column(ForeignKey("reservations_clean.id", ondelete="CASCADE"), nullable=False)
    feature_id: Mapped[int | None] = mapped_column(ForeignKey("reservation_features.id", ondelete="SET NULL"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_class: Mapped[str] = mapped_column(String(16), nullable=False)
    threshold_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    scoring_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reservation: Mapped["ReservationClean"] = relationship(back_populates="predictions")
    feature: Mapped["ReservationFeature | None"] = relationship(back_populates="predictions")
    actions: Mapped[list["ReservationAction"]] = relationship(back_populates="prediction")

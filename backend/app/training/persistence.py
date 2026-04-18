from __future__ import annotations

import json
import shutil
from datetime import date
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.prediction import Prediction
from app.models.reservation import ReservationClean, ReservationFeature, ReservationImportBatch, ReservationRaw


def to_native_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def dataframe_to_json_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        records.append({key: to_native_value(value) for key, value in record.items()})
    return records


def _parse_optional_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _parse_optional_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def refresh_latest_artifacts(run_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(run_dir, latest_dir)


def persist_training_outputs_to_database(
    database_url: str,
    *,
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    prediction_frames: dict[str, pd.DataFrame],
    feature_set_version: str,
    source_name: str = "hotel_booking_demand_h1_h2",
) -> dict[str, int]:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with session_factory() as session:
        batch = ReservationImportBatch(
            source_name=source_name,
            source_files=sorted(raw_df["source_file"].dropna().unique().tolist()),
            status="completed",
            row_count=int(len(raw_df)),
            error_count=0,
            metadata_payload={
                "feature_set_version": feature_set_version,
                "persisted_at": datetime.now(timezone.utc).isoformat(),
            },
            completed_at=datetime.now(timezone.utc),
        )
        session.add(batch)
        session.flush()

        raw_records = []
        source_columns = [column for column in raw_df.columns if column not in {"source_file", "source_row_number", "reservation_key"}]
        for record in dataframe_to_json_records(raw_df):
            raw_payload = {column: record.get(column) for column in source_columns}
            raw_records.append(
                {
                    "batch_id": batch.id,
                    "source_file": record["source_file"],
                    "source_row_number": int(record["source_row_number"]),
                    "property_code": record.get("source_file"),
                    "raw_payload": raw_payload,
                    "reservation_status": record.get("ReservationStatus"),
                    "reservation_status_date": _parse_optional_date(record.get("ReservationStatusDate")),
                }
            )
        session.execute(insert(ReservationRaw), raw_records)
        session.flush()

        raw_id_map = {
            (row.source_file, row.source_row_number): row.id
            for row in session.execute(
                select(ReservationRaw.id, ReservationRaw.source_file, ReservationRaw.source_row_number).where(
                    ReservationRaw.batch_id == batch.id
                )
            )
        }

        clean_records = []
        for record in dataframe_to_json_records(clean_df):
            raw_id = raw_id_map[(record["source_file"], int(record["source_row_number"]))]
            clean_records.append(
                {
                    "raw_reservation_id": raw_id,
                    "batch_id": batch.id,
                    "property_id": record["property_id"],
                    "source_file": record["source_file"],
                    "arrival_date": _parse_optional_date(record.get("arrival_date")),
                    "lead_time_days": record.get("lead_time_days"),
                    "arrival_year": record.get("arrival_year"),
                    "arrival_month_name": record.get("arrival_month_name"),
                    "arrival_week_number": record.get("arrival_week_number"),
                    "arrival_day_of_month": record.get("arrival_day_of_month"),
                    "weekend_nights": record.get("weekend_nights"),
                    "week_nights": record.get("week_nights"),
                    "adults": record.get("adults"),
                    "children": record.get("children"),
                    "babies": record.get("babies"),
                    "meal_plan": record.get("meal_plan"),
                    "country_code": record.get("country_code"),
                    "market_segment": record.get("market_segment"),
                    "distribution_channel": record.get("distribution_channel"),
                    "is_repeated_guest": record.get("is_repeated_guest"),
                    "previous_cancellations": record.get("previous_cancellations"),
                    "previous_non_cancelled_bookings": record.get("previous_non_cancelled_bookings"),
                    "reserved_room_type": record.get("reserved_room_type"),
                    "deposit_type": record.get("deposit_type"),
                    "agent_code": record.get("agent_code"),
                    "company_code": record.get("company_code"),
                    "customer_type": record.get("customer_type"),
                    "adr": record.get("adr"),
                    "required_car_parking_spaces": record.get("required_car_parking_spaces"),
                    "total_special_requests": record.get("total_special_requests"),
                    "booking_changes": record.get("booking_changes"),
                    "days_in_waiting_list": record.get("days_in_waiting_list"),
                    "assigned_room_type": record.get("assigned_room_type"),
                    "reservation_status": record.get("reservation_status"),
                    "reservation_status_date": _parse_optional_date(record.get("reservation_status_date")),
                    "is_canceled": bool(record["is_canceled"]) if record.get("is_canceled") is not None else None,
                    "no_show_flag": bool(record["no_show_flag"]) if record.get("no_show_flag") is not None else None,
                    "excluded_from_training": bool(record["excluded_from_training"]),
                    "exclusion_reason": record.get("exclusion_reason"),
                }
            )
        session.execute(insert(ReservationClean), clean_records)
        session.flush()

        clean_id_map = {
            (row.source_file, row.source_row_number): row.id
            for row in session.execute(
                select(ReservationClean.id, ReservationRaw.source_file, ReservationRaw.source_row_number)
                .join(ReservationRaw, ReservationClean.raw_reservation_id == ReservationRaw.id)
                .where(ReservationClean.batch_id == batch.id)
            )
        }

        feature_records = []
        for record in dataframe_to_json_records(feature_df):
            clean_id = clean_id_map[(record["source_file"], int(record["source_row_number"]))]
            feature_payload = {
                key: record.get(key)
                for key in record.keys()
                if key
                not in {
                    "source_file",
                    "source_row_number",
                    "reservation_key",
                    "feature_set_version",
                }
            }
            feature_records.append(
                {
                    "reservation_clean_id": clean_id,
                    "feature_set_version": record["feature_set_version"],
                    "total_nights": record.get("total_nights"),
                    "total_guests": record.get("total_guests"),
                    "has_children": bool(record["has_children"]) if record.get("has_children") is not None else None,
                    "is_family": bool(record["is_family"]) if record.get("is_family") is not None else None,
                    "lead_time_bucket": record.get("lead_time_bucket"),
                    "has_agent": bool(record["has_agent"]) if record.get("has_agent") is not None else None,
                    "has_company": bool(record["has_company"]) if record.get("has_company") is not None else None,
                    "special_request_flag": bool(record["special_request_flag"]) if record.get("special_request_flag") is not None else None,
                    "adr_per_guest": record.get("adr_per_guest"),
                    "adr_per_night_proxy": record.get("adr_per_night_proxy"),
                    "is_high_season": bool(record["is_high_season"]) if record.get("is_high_season") is not None else None,
                    "is_weekend_heavy": bool(record["is_weekend_heavy"]) if record.get("is_weekend_heavy") is not None else None,
                    "previous_cancel_ratio": record.get("previous_cancel_ratio"),
                    "feature_payload": feature_payload,
                }
            )
        session.execute(insert(ReservationFeature), feature_records)
        session.flush()

        feature_id_map = {
            (row.source_file, row.source_row_number): row.id
            for row in session.execute(
                select(ReservationFeature.id, ReservationRaw.source_file, ReservationRaw.source_row_number)
                .join(ReservationClean, ReservationFeature.reservation_clean_id == ReservationClean.id)
                .join(ReservationRaw, ReservationClean.raw_reservation_id == ReservationRaw.id)
                .where(ReservationClean.batch_id == batch.id)
            )
        }

        total_prediction_rows = 0
        for prediction_frame in prediction_frames.values():
            prediction_records = []
            for record in dataframe_to_json_records(prediction_frame):
                key = (record["source_file"], int(record["source_row_number"]))
                prediction_records.append(
                    {
                        "reservation_clean_id": clean_id_map[key],
                        "feature_id": feature_id_map.get(key),
                        "model_name": record["model_name"],
                        "model_version": record["model_version"],
                        "score": record["score"],
                        "risk_class": record["risk_class"],
                        "threshold_used": record["threshold_used"],
                        "scoring_run_id": record["scoring_run_id"],
                        "metadata_payload": {
                            "model_stage": record.get("model_stage"),
                            "snapshot_stage": record.get("snapshot_stage"),
                            "snapshot_at": record.get("snapshot_at"),
                            "days_since_booking": record.get("days_since_booking"),
                            "days_to_arrival": record.get("days_to_arrival"),
                            "split_name": record["split_name"],
                            "feature_set_version": record["feature_set_version"],
                            "actual_no_show_flag": record["actual_no_show_flag"],
                            "reservation_key": record["reservation_key"],
                        },
                        "scored_at": _parse_optional_datetime(record["scored_at"]),
                    }
                )
            session.execute(insert(Prediction), prediction_records)
            total_prediction_rows += len(prediction_records)

        session.commit()

        return {
            "reservation_import_batches": 1,
            "reservations_raw": len(raw_records),
            "reservations_clean": len(clean_records),
            "reservation_features": len(feature_records),
            "predictions": total_prediction_rows,
        }

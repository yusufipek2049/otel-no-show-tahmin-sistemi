from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.prediction import Prediction
from app.models.reservation import ReservationClean, ReservationFeature, ReservationImportBatch, ReservationRaw
from app.training.constants import FEATURE_SET_VERSION
from app.training.features import build_dataset_bundle
from app.training.persistence import persist_training_outputs_to_database
from app.training.split import temporal_train_test_split
from app.training.stages import ModelStage


def _build_fixture_dataframe() -> pd.DataFrame:
    rows = [
        {
            "IsCanceled": "0",
            "LeadTime": "10",
            "ArrivalDateYear": "2015",
            "ArrivalDateMonth": "July",
            "ArrivalDateWeekNumber": "27",
            "ArrivalDateDayOfMonth": "1",
            "StaysInWeekendNights": "1",
            "StaysInWeekNights": "2",
            "Adults": "2",
            "Children": "0",
            "Babies": "0",
            "Meal": "BB       ",
            "Country": "PRT",
            "MarketSegment": "Direct",
            "DistributionChannel": "Direct",
            "IsRepeatedGuest": "0",
            "PreviousCancellations": "0",
            "PreviousBookingsNotCanceled": "0",
            "ReservedRoomType": "A               ",
            "AssignedRoomType": "A               ",
            "BookingChanges": "1",
            "DepositType": "No Deposit     ",
            "Agent": "       NULL",
            "Company": "       NULL",
            "DaysInWaitingList": "0",
            "CustomerType": "Transient",
            "ADR": "100",
            "RequiredCarParkingSpaces": "0",
            "TotalOfSpecialRequests": "1",
            "ReservationStatus": "Check-Out",
            "ReservationStatusDate": "2015-07-01",
            "source_file": "H1.csv",
            "source_row_number": 1,
            "reservation_key": "H1.csv:1",
        },
        {
            "IsCanceled": "0",
            "LeadTime": "30",
            "ArrivalDateYear": "2016",
            "ArrivalDateMonth": "August",
            "ArrivalDateWeekNumber": "31",
            "ArrivalDateDayOfMonth": "10",
            "StaysInWeekendNights": "2",
            "StaysInWeekNights": "3",
            "Adults": "2",
            "Children": "1",
            "Babies": "0",
            "Meal": "HB       ",
            "Country": "GBR",
            "MarketSegment": "Online TA",
            "DistributionChannel": "TA/TO",
            "IsRepeatedGuest": "1",
            "PreviousCancellations": "1",
            "PreviousBookingsNotCanceled": "2",
            "ReservedRoomType": "B               ",
            "AssignedRoomType": "B               ",
            "BookingChanges": "0",
            "DepositType": "No Deposit     ",
            "Agent": "          9",
            "Company": "       NULL",
            "DaysInWaitingList": "0",
            "CustomerType": "Transient",
            "ADR": "120",
            "RequiredCarParkingSpaces": "1",
            "TotalOfSpecialRequests": "2",
            "ReservationStatus": "No-Show",
            "ReservationStatusDate": "2016-08-10",
            "source_file": "H2.csv",
            "source_row_number": 1,
            "reservation_key": "H2.csv:1",
        },
        {
            "IsCanceled": "0",
            "LeadTime": "5",
            "ArrivalDateYear": "2017",
            "ArrivalDateMonth": "July",
            "ArrivalDateWeekNumber": "28",
            "ArrivalDateDayOfMonth": "11",
            "StaysInWeekendNights": "1",
            "StaysInWeekNights": "1",
            "Adults": "1",
            "Children": "0",
            "Babies": "0",
            "Meal": "BB       ",
            "Country": "ESP",
            "MarketSegment": "Corporate",
            "DistributionChannel": "Corporate",
            "IsRepeatedGuest": "0",
            "PreviousCancellations": "0",
            "PreviousBookingsNotCanceled": "1",
            "ReservedRoomType": "C               ",
            "AssignedRoomType": "C               ",
            "BookingChanges": "0",
            "DepositType": "No Deposit     ",
            "Agent": "       NULL",
            "Company": "       NULL",
            "DaysInWaitingList": "0",
            "CustomerType": "Contract",
            "ADR": "90",
            "RequiredCarParkingSpaces": "0",
            "TotalOfSpecialRequests": "0",
            "ReservationStatus": "Check-Out",
            "ReservationStatusDate": "2017-07-11",
            "source_file": "H1.csv",
            "source_row_number": 2,
            "reservation_key": "H1.csv:2",
        },
        {
            "IsCanceled": "1",
            "LeadTime": "50",
            "ArrivalDateYear": "2017",
            "ArrivalDateMonth": "September",
            "ArrivalDateWeekNumber": "36",
            "ArrivalDateDayOfMonth": "15",
            "StaysInWeekendNights": "0",
            "StaysInWeekNights": "2",
            "Adults": "2",
            "Children": "0",
            "Babies": "0",
            "Meal": "BB       ",
            "Country": "PRT",
            "MarketSegment": "Online TA",
            "DistributionChannel": "TA/TO",
            "IsRepeatedGuest": "0",
            "PreviousCancellations": "0",
            "PreviousBookingsNotCanceled": "0",
            "ReservedRoomType": "A               ",
            "AssignedRoomType": "A               ",
            "BookingChanges": "1",
            "DepositType": "Non Refund",
            "Agent": "         14",
            "Company": "       NULL",
            "DaysInWaitingList": "5",
            "CustomerType": "Transient",
            "ADR": "110",
            "RequiredCarParkingSpaces": "0",
            "TotalOfSpecialRequests": "1",
            "ReservationStatus": "Canceled",
            "ReservationStatusDate": "2017-08-01",
            "source_file": "H2.csv",
            "source_row_number": 2,
            "reservation_key": "H2.csv:2",
        },
    ]
    return pd.DataFrame(rows)


def _build_snapshot_fixture_dataframe() -> pd.DataFrame:
    rows = [
        {
            "reservation_key": "snapshot:1",
            "source_file": "snapshot_day_1.csv",
            "source_row_number": 1,
            "property_id": "RESORT_H1",
            "arrival_date": "2015-07-05",
            "lead_time_days": 34,
            "arrival_year": 2015,
            "arrival_month_name": "July",
            "arrival_week_number": 27,
            "arrival_day_of_month": 5,
            "weekend_nights": 1,
            "week_nights": 2,
            "adults": 2,
            "children": 0,
            "babies": 0,
            "meal_plan": "BB",
            "country_code": "PRT",
            "market_segment": "Direct",
            "distribution_channel": "Direct",
            "is_repeated_guest": 0,
            "previous_cancellations": 0,
            "previous_non_cancelled_bookings": 1,
            "reserved_room_type": "A",
            "deposit_type": "No Deposit",
            "agent_code": pd.NA,
            "company_code": pd.NA,
            "customer_type": "Transient",
            "adr": 100,
            "required_car_parking_spaces": 0,
            "total_special_requests": 1,
            "snapshot_stage": "post_booking_day_1",
            "snapshot_at": "2015-06-02T00:00:00+00:00",
            "days_since_booking": 1,
            "days_to_arrival": 33,
            "is_active_at_snapshot": "true",
            "final_outcome": "Check-Out",
            "booking_changes_as_of_cutoff": 0,
            "days_in_waiting_list_as_of_cutoff": 0,
            "assigned_room_type_as_of_cutoff": pd.NA,
            "days_since_last_booking_change": pd.NA,
            "days_since_room_assignment": pd.NA,
        },
        {
            "reservation_key": "snapshot:2",
            "source_file": "snapshot_day_1.csv",
            "source_row_number": 2,
            "property_id": "CITY_H2",
            "arrival_date": "2016-08-10",
            "lead_time_days": 20,
            "arrival_year": 2016,
            "arrival_month_name": "August",
            "arrival_week_number": 32,
            "arrival_day_of_month": 10,
            "weekend_nights": 2,
            "week_nights": 3,
            "adults": 2,
            "children": 1,
            "babies": 0,
            "meal_plan": "HB",
            "country_code": "GBR",
            "market_segment": "Online TA",
            "distribution_channel": "TA/TO",
            "is_repeated_guest": 1,
            "previous_cancellations": 1,
            "previous_non_cancelled_bookings": 2,
            "reserved_room_type": "B",
            "deposit_type": "No Deposit",
            "agent_code": "9",
            "company_code": pd.NA,
            "customer_type": "Transient",
            "adr": 120,
            "required_car_parking_spaces": 1,
            "total_special_requests": 2,
            "snapshot_stage": "post_booking_day_1",
            "snapshot_at": "2016-07-02T00:00:00+00:00",
            "days_since_booking": 1,
            "days_to_arrival": 39,
            "is_active_at_snapshot": "true",
            "final_outcome": "No-Show",
            "booking_changes_as_of_cutoff": 1,
            "days_in_waiting_list_as_of_cutoff": 0,
            "assigned_room_type_as_of_cutoff": "B",
            "days_since_last_booking_change": 1,
            "days_since_room_assignment": 0,
        },
        {
            "reservation_key": "snapshot:3",
            "source_file": "snapshot_day_1.csv",
            "source_row_number": 3,
            "property_id": "RESORT_H1",
            "arrival_date": "2017-07-11",
            "lead_time_days": 7,
            "arrival_year": 2017,
            "arrival_month_name": "July",
            "arrival_week_number": 28,
            "arrival_day_of_month": 11,
            "weekend_nights": 1,
            "week_nights": 1,
            "adults": 1,
            "children": 0,
            "babies": 0,
            "meal_plan": "BB",
            "country_code": "ESP",
            "market_segment": "Corporate",
            "distribution_channel": "Corporate",
            "is_repeated_guest": 0,
            "previous_cancellations": 0,
            "previous_non_cancelled_bookings": 1,
            "reserved_room_type": "C",
            "deposit_type": "No Deposit",
            "agent_code": pd.NA,
            "company_code": pd.NA,
            "customer_type": "Contract",
            "adr": 90,
            "required_car_parking_spaces": 0,
            "total_special_requests": 0,
            "snapshot_stage": "post_booking_day_1",
            "snapshot_at": "2017-07-01T00:00:00+00:00",
            "days_since_booking": 1,
            "days_to_arrival": 10,
            "is_active_at_snapshot": "true",
            "final_outcome": "Check-Out",
            "booking_changes_as_of_cutoff": 0,
            "days_in_waiting_list_as_of_cutoff": 2,
            "assigned_room_type_as_of_cutoff": "C",
            "days_since_last_booking_change": pd.NA,
            "days_since_room_assignment": 0,
        },
        {
            "reservation_key": "snapshot:4",
            "source_file": "snapshot_day_1.csv",
            "source_row_number": 4,
            "property_id": "CITY_H2",
            "arrival_date": "2017-09-15",
            "lead_time_days": 50,
            "arrival_year": 2017,
            "arrival_month_name": "September",
            "arrival_week_number": 36,
            "arrival_day_of_month": 15,
            "weekend_nights": 0,
            "week_nights": 2,
            "adults": 2,
            "children": 0,
            "babies": 0,
            "meal_plan": "BB",
            "country_code": "PRT",
            "market_segment": "Online TA",
            "distribution_channel": "TA/TO",
            "is_repeated_guest": 0,
            "previous_cancellations": 0,
            "previous_non_cancelled_bookings": 0,
            "reserved_room_type": "A",
            "deposit_type": "Non Refund",
            "agent_code": "14",
            "company_code": pd.NA,
            "customer_type": "Transient",
            "adr": 110,
            "required_car_parking_spaces": 0,
            "total_special_requests": 1,
            "snapshot_stage": "post_booking_day_1",
            "snapshot_at": "2017-08-01T00:00:00+00:00",
            "days_since_booking": 1,
            "days_to_arrival": 45,
            "is_active_at_snapshot": "false",
            "final_outcome": "Canceled",
            "booking_changes_as_of_cutoff": 1,
            "days_in_waiting_list_as_of_cutoff": 5,
            "assigned_room_type_as_of_cutoff": pd.NA,
            "days_since_last_booking_change": 0,
            "days_since_room_assignment": pd.NA,
        },
    ]
    return pd.DataFrame(rows)


def test_dataset_bundle_excludes_canceled_rows_and_forbidden_features() -> None:
    bundle = build_dataset_bundle(_build_fixture_dataframe())

    assert bundle.import_summary["row_count_raw"] == 4
    assert bundle.import_summary["row_count_training"] == 3
    assert "reservation_status" not in bundle.modeling_df.columns
    assert "is_canceled" not in bundle.modeling_df.columns
    assert "booking_changes" not in bundle.modeling_df.columns
    assert "days_in_waiting_list" not in bundle.modeling_df.columns
    assert "assigned_room_type" not in bundle.modeling_df.columns
    assert set(bundle.modeling_df["no_show_flag"].unique()) == {0, 1}


def test_temporal_split_uses_expected_years() -> None:
    bundle = build_dataset_bundle(_build_fixture_dataframe())
    split_bundle = temporal_train_test_split(bundle.modeling_df, stage_config=bundle.stage_config)

    assert set(split_bundle.train_df["arrival_year"].unique()) == {2015, 2016}
    assert set(split_bundle.test_df["arrival_year"].unique()) == {2017}


def test_snapshot_stage_bundle_requires_snapshot_contract_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        build_dataset_bundle(_build_fixture_dataframe(), model_stage=ModelStage.POST_BOOKING_DAY_1)


def test_snapshot_stage_bundle_uses_stage_policy_and_snapshot_year_split() -> None:
    bundle = build_dataset_bundle(_build_snapshot_fixture_dataframe(), model_stage=ModelStage.POST_BOOKING_DAY_1)
    split_bundle = temporal_train_test_split(bundle.modeling_df, stage_config=bundle.stage_config)

    assert bundle.import_summary["model_stage"] == ModelStage.POST_BOOKING_DAY_1.value
    assert bundle.stage_config.split_year_column == "snapshot_year"
    assert "booking_changes_as_of_cutoff" in bundle.modeling_df.columns
    assert "has_any_booking_change_as_of_cutoff" in bundle.modeling_df.columns
    assert "waiting_list_flag_as_of_cutoff" in bundle.modeling_df.columns
    assert "room_assigned_flag_as_of_cutoff" in bundle.modeling_df.columns
    assert "final_outcome" not in bundle.modeling_df.columns
    assert set(split_bundle.train_df["snapshot_year"].unique()) == {2015, 2016}
    assert set(split_bundle.test_df["snapshot_year"].unique()) == {2017}


def test_prediction_records_can_be_persisted_to_sqlite(tmp_path: Path) -> None:
    bundle = build_dataset_bundle(_build_fixture_dataframe())

    prediction_frame = pd.DataFrame(
        [
            {
                "reservation_key": "H1.csv:2",
                "source_file": "H1.csv",
                "source_row_number": 2,
                "arrival_date": "2017-07-11T00:00:00",
                "actual_no_show_flag": 0,
                "feature_set_version": FEATURE_SET_VERSION,
                "split_name": "test",
                "model_name": "logistic_regression",
                "model_version": "logreg_test",
                "score": 0.42,
                "risk_class": "medium",
                "threshold_used": 0.35,
                "scoring_run_id": "test-run",
                "scored_at": "2026-04-12T00:00:00+00:00",
                "model_stage": ModelStage.BOOKING_TIME.value,
                "snapshot_stage": ModelStage.BOOKING_TIME.value,
                "days_since_booking": 0,
                "days_to_arrival": 5,
            }
        ]
    )

    database_url = f"sqlite:///{tmp_path / 'training.db'}"
    summary = persist_training_outputs_to_database(
        database_url,
        raw_df=bundle.raw_df,
        clean_df=bundle.clean_df,
        feature_df=bundle.feature_df,
        prediction_frames={"logistic_regression": prediction_frame},
        feature_set_version=FEATURE_SET_VERSION,
    )

    assert summary["reservations_raw"] == 4
    assert summary["reservations_clean"] == 4
    assert summary["reservation_features"] == 4
    assert summary["predictions"] == 1

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ReservationImportBatch)) == 1
        assert session.scalar(select(func.count()).select_from(ReservationRaw)) == 4
        assert session.scalar(select(func.count()).select_from(ReservationClean)) == 4
        assert session.scalar(select(func.count()).select_from(ReservationFeature)) == 4
        assert session.scalar(select(func.count()).select_from(Prediction)) == 1
        prediction = session.scalar(select(Prediction))
        assert prediction is not None
        assert prediction.metadata_payload["model_stage"] == ModelStage.BOOKING_TIME.value
        assert prediction.metadata_payload["snapshot_stage"] == ModelStage.BOOKING_TIME.value
        assert prediction.metadata_payload["days_since_booking"] == 0

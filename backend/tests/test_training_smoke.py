from __future__ import annotations

import pandas as pd

from app.training.features import build_dataset_bundle
from app.training.pipeline import run_training_pipeline
from app.training.split import temporal_train_test_split
from app.training.stages import ModelStage


def _small_raw_reservation_frame() -> pd.DataFrame:
    base = {
        "IsCanceled": "0",
        "LeadTime": "10",
        "ArrivalDateMonth": "July",
        "ArrivalDateWeekNumber": "27",
        "ArrivalDateDayOfMonth": "1",
        "StaysInWeekendNights": "1",
        "StaysInWeekNights": "2",
        "Adults": "2",
        "Children": "0",
        "Babies": "0",
        "Meal": "BB",
        "Country": "PRT",
        "MarketSegment": "Direct",
        "DistributionChannel": "Direct",
        "IsRepeatedGuest": "0",
        "PreviousCancellations": "0",
        "PreviousBookingsNotCanceled": "0",
        "ReservedRoomType": "A",
        "AssignedRoomType": "A",
        "BookingChanges": "0",
        "DepositType": "No Deposit",
        "Agent": "NULL",
        "Company": "NULL",
        "DaysInWaitingList": "0",
        "CustomerType": "Transient",
        "ADR": "100",
        "RequiredCarParkingSpaces": "0",
        "TotalOfSpecialRequests": "1",
    }
    rows = []
    for index, (year, status) in enumerate(
        [(2015, "Check-Out"), (2016, "No-Show"), (2017, "Check-Out")],
        start=1,
    ):
        row = {
            **base,
            "ArrivalDateYear": str(year),
            "ReservationStatus": status,
            "ReservationStatusDate": f"{year}-07-01",
            "source_file": "H1.csv",
            "source_row_number": index,
            "reservation_key": f"H1.csv:{index}",
        }
        rows.append(row)
    return pd.DataFrame(rows)


def test_training_pipeline_components_are_importable() -> None:
    assert callable(build_dataset_bundle)
    assert callable(temporal_train_test_split)
    assert callable(run_training_pipeline)


def test_training_smoke_builds_dataset_and_temporal_split_without_full_training() -> None:
    bundle = build_dataset_bundle(_small_raw_reservation_frame(), model_stage=ModelStage.BOOKING_TIME)
    split = temporal_train_test_split(bundle.modeling_df, stage_config=bundle.stage_config)

    assert bundle.import_summary["row_count_training"] == 3
    assert len(bundle.modeling_df) == 3
    assert set(split.train_df["arrival_year"]) == {2015, 2016}
    assert set(split.test_df["arrival_year"]) == {2017}


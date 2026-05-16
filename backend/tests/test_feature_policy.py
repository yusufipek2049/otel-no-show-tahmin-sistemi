from __future__ import annotations

import pandas as pd
import pytest

from app.training.features import enforce_feature_policy
from app.training.stages import ModelStage, get_model_stage_config


def _valid_booking_time_modeling_frame() -> pd.DataFrame:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    row = {
        "reservation_key": "fixture:1",
        "source_file": "H1.csv",
        "source_row_number": 1,
        "arrival_date": "2017-07-01",
        "model_stage": ModelStage.BOOKING_TIME.value,
        "feature_set_version": stage_config.feature_set_version,
        "arrival_year": 2017,
        "no_show_flag": 0,
    }
    for column in stage_config.feature_policy.model_feature_columns:
        row[column] = "A" if column in stage_config.feature_policy.categorical_feature_columns else 0
    return pd.DataFrame([row])


def test_leakage_prone_internal_column_raises() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = _valid_booking_time_modeling_frame()
    modeling_df["reservation_status"] = "No-Show"

    with pytest.raises(ValueError, match="Leakage-prone internal columns"):
        enforce_feature_policy(modeling_df, stage_config.feature_policy)


def test_leakage_prone_source_column_raises() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = _valid_booking_time_modeling_frame()
    modeling_df["ReservationStatus"] = "No-Show"

    with pytest.raises(ValueError, match="Leakage-prone source columns"):
        enforce_feature_policy(modeling_df, stage_config.feature_policy)


def test_missing_expected_feature_column_raises() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = _valid_booking_time_modeling_frame().drop(columns=["lead_time_days"])

    with pytest.raises(ValueError, match="Expected feature columns are missing"):
        enforce_feature_policy(modeling_df, stage_config.feature_policy)


def test_booking_time_safe_feature_set_passes() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = _valid_booking_time_modeling_frame()

    enforce_feature_policy(modeling_df, stage_config.feature_policy)


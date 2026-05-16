from __future__ import annotations

import pandas as pd
import pytest

from app.training.split import temporal_train_test_split
from app.training.stages import ModelStage, get_model_stage_config


def test_temporal_split_uses_2015_2016_train_and_2017_test() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = pd.DataFrame(
        {
            "arrival_year": [2015, 2016, 2017],
            "no_show_flag": [0, 1, 0],
        }
    )

    split = temporal_train_test_split(modeling_df, stage_config=stage_config)

    assert set(split.train_df["arrival_year"]) == {2015, 2016}
    assert set(split.test_df["arrival_year"]) == {2017}
    assert split.split_year_column == "arrival_year"


def test_temporal_split_raises_when_train_is_empty() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = pd.DataFrame({"arrival_year": [2017], "no_show_flag": [0]})

    with pytest.raises(ValueError, match="No training rows"):
        temporal_train_test_split(modeling_df, stage_config=stage_config)


def test_temporal_split_raises_when_test_is_empty() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = pd.DataFrame({"arrival_year": [2015, 2016], "no_show_flag": [0, 1]})

    with pytest.raises(ValueError, match="No test rows"):
        temporal_train_test_split(modeling_df, stage_config=stage_config)


def test_temporal_split_raises_when_split_year_column_is_missing() -> None:
    stage_config = get_model_stage_config(ModelStage.BOOKING_TIME)
    modeling_df = pd.DataFrame({"no_show_flag": [0, 1]})

    with pytest.raises(ValueError, match="Split year column"):
        temporal_train_test_split(modeling_df, stage_config=stage_config)


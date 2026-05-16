from __future__ import annotations

import pandas as pd

from app.core.logging import get_logger, log_event
from app.training.constants import TEST_YEARS, TRAIN_YEARS
from app.training.schemas import TemporalSplitBundle
from app.training.stages import ModelStageConfig, get_model_stage_config

logger = get_logger(__name__)


def temporal_train_test_split(
    modeling_df: pd.DataFrame,
    *,
    stage_config: ModelStageConfig | None = None,
    train_years: tuple[int, ...] = TRAIN_YEARS,
    test_years: tuple[int, ...] = TEST_YEARS,
) -> TemporalSplitBundle:
    resolved_stage_config = stage_config or get_model_stage_config("booking_time")
    split_year_column = resolved_stage_config.split_year_column

    if split_year_column not in modeling_df.columns:
        logger.error(log_event("temporal_split_failed", reason="split_year_column_missing", split_year_column=split_year_column))
        raise ValueError(f"Split year column '{split_year_column}' is missing from the modeling dataset.")

    train_df = modeling_df.loc[modeling_df[split_year_column].isin(train_years)].copy()
    test_df = modeling_df.loc[modeling_df[split_year_column].isin(test_years)].copy()

    if train_df.empty:
        logger.error(log_event("temporal_split_failed", reason="empty_train_split", train_years=",".join(map(str, train_years))))
        raise ValueError(f"No training rows found for train years {train_years}.")
    if test_df.empty:
        logger.error(log_event("temporal_split_failed", reason="empty_test_split", test_years=",".join(map(str, test_years))))
        raise ValueError(f"No test rows found for test years {test_years}.")

    logger.info(
        log_event(
            "temporal_split",
            stage=resolved_stage_config.stage.value,
            split_year_column=split_year_column,
            train_years=",".join(map(str, sorted(train_df[split_year_column].unique().tolist()))),
            test_years=",".join(map(str, sorted(test_df[split_year_column].unique().tolist()))),
            train_rows=len(train_df),
            test_rows=len(test_df),
        )
    )
    return TemporalSplitBundle(train_df=train_df, test_df=test_df, split_year_column=split_year_column)

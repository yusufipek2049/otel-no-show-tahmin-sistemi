from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.training.constants import (
    BASE_MODEL_FEATURE_COLUMNS,
    CATEGORICAL_FEATURE_COLUMNS,
    DEFAULT_ARTIFACTS_ROOT,
    ENGINEERED_FEATURE_COLUMNS,
    EXCLUDED_INTERNAL_COLUMNS,
    EXCLUDED_SOURCE_COLUMNS,
    FEATURE_SET_VERSION,
    NUMERIC_FEATURE_COLUMNS,
)


def _unique_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


class ModelStage(str, Enum):
    BOOKING_TIME = "booking_time"
    POST_BOOKING_DAY_1 = "post_booking_day_1"
    POST_BOOKING_DAY_2 = "post_booking_day_2"
    POST_BOOKING_DAY_3 = "post_booking_day_3"
    POST_BOOKING_DAY_4 = "post_booking_day_4"


@dataclass(frozen=True)
class StageFeaturePolicy:
    feature_set_version: str
    base_feature_columns: tuple[str, ...]
    engineered_feature_columns: tuple[str, ...]
    numeric_feature_columns: tuple[str, ...]
    categorical_feature_columns: tuple[str, ...]
    excluded_source_columns: tuple[str, ...]
    excluded_internal_columns: tuple[str, ...]

    @property
    def model_feature_columns(self) -> tuple[str, ...]:
        return self.base_feature_columns + self.engineered_feature_columns

    def to_machine_readable_dict(self) -> dict[str, object]:
        return {
            "feature_set_version": self.feature_set_version,
            "model_feature_columns": list(self.model_feature_columns),
            "numeric_feature_columns": list(self.numeric_feature_columns),
            "categorical_feature_columns": list(self.categorical_feature_columns),
            "excluded_source_columns": list(self.excluded_source_columns),
            "excluded_internal_columns": list(self.excluded_internal_columns),
        }


@dataclass(frozen=True)
class ModelStageConfig:
    stage: ModelStage
    description: str
    requires_snapshot_data: bool
    split_year_column: str
    snapshot_day_offset: int | None
    feature_policy: StageFeaturePolicy

    @property
    def feature_set_version(self) -> str:
        return self.feature_policy.feature_set_version


SNAPSHOT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "reservation_key",
    "source_file",
    "source_row_number",
    "property_id",
    "arrival_date",
    "lead_time_days",
    "arrival_year",
    "arrival_month_name",
    "arrival_week_number",
    "arrival_day_of_month",
    "weekend_nights",
    "week_nights",
    "adults",
    "children",
    "babies",
    "meal_plan",
    "country_code",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_non_cancelled_bookings",
    "reserved_room_type",
    "deposit_type",
    "agent_code",
    "company_code",
    "customer_type",
    "adr",
    "required_car_parking_spaces",
    "total_special_requests",
    "snapshot_stage",
    "snapshot_at",
    "days_since_booking",
    "days_to_arrival",
    "is_active_at_snapshot",
    "final_outcome",
)

SNAPSHOT_OPTIONAL_COLUMNS: tuple[str, ...] = (
    "booking_changes_as_of_cutoff",
    "days_in_waiting_list_as_of_cutoff",
    "assigned_room_type_as_of_cutoff",
    "days_since_last_booking_change",
    "days_since_room_assignment",
)

POST_BOOKING_BASE_FEATURE_COLUMNS: tuple[str, ...] = (
    *tuple(BASE_MODEL_FEATURE_COLUMNS),
    "days_since_booking",
    "days_to_arrival",
    "booking_changes_as_of_cutoff",
    "days_in_waiting_list_as_of_cutoff",
    "assigned_room_type_as_of_cutoff",
    "days_since_last_booking_change",
    "days_since_room_assignment",
)

POST_BOOKING_ENGINEERED_FEATURE_COLUMNS: tuple[str, ...] = (
    *tuple(ENGINEERED_FEATURE_COLUMNS),
    "has_any_booking_change_as_of_cutoff",
    "waiting_list_flag_as_of_cutoff",
    "room_assigned_flag_as_of_cutoff",
)

POST_BOOKING_NUMERIC_FEATURE_COLUMNS: tuple[str, ...] = _unique_tuple(
    (
        *tuple(NUMERIC_FEATURE_COLUMNS),
        "days_since_booking",
        "days_to_arrival",
        "booking_changes_as_of_cutoff",
        "days_in_waiting_list_as_of_cutoff",
        "days_since_last_booking_change",
        "days_since_room_assignment",
        "has_any_booking_change_as_of_cutoff",
        "waiting_list_flag_as_of_cutoff",
        "room_assigned_flag_as_of_cutoff",
    )
)

POST_BOOKING_CATEGORICAL_FEATURE_COLUMNS: tuple[str, ...] = _unique_tuple(
    (*tuple(CATEGORICAL_FEATURE_COLUMNS), "assigned_room_type_as_of_cutoff")
)

POST_BOOKING_EXCLUDED_INTERNAL_COLUMNS: tuple[str, ...] = _unique_tuple(
    (
        *tuple(EXCLUDED_INTERNAL_COLUMNS),
        "final_outcome",
        "snapshot_stage",
        "snapshot_at",
        "snapshot_year",
        "is_active_at_snapshot",
    )
)

BOOKING_TIME_POLICY = StageFeaturePolicy(
    feature_set_version=FEATURE_SET_VERSION,
    base_feature_columns=tuple(BASE_MODEL_FEATURE_COLUMNS),
    engineered_feature_columns=tuple(ENGINEERED_FEATURE_COLUMNS),
    numeric_feature_columns=tuple(NUMERIC_FEATURE_COLUMNS),
    categorical_feature_columns=tuple(CATEGORICAL_FEATURE_COLUMNS),
    excluded_source_columns=tuple(EXCLUDED_SOURCE_COLUMNS),
    excluded_internal_columns=tuple(EXCLUDED_INTERNAL_COLUMNS),
)

POST_BOOKING_FEATURE_POLICIES = {
    stage: StageFeaturePolicy(
        feature_set_version=f"{stage.value}_v1",
        base_feature_columns=POST_BOOKING_BASE_FEATURE_COLUMNS,
        engineered_feature_columns=POST_BOOKING_ENGINEERED_FEATURE_COLUMNS,
        numeric_feature_columns=POST_BOOKING_NUMERIC_FEATURE_COLUMNS,
        categorical_feature_columns=POST_BOOKING_CATEGORICAL_FEATURE_COLUMNS,
        excluded_source_columns=tuple(EXCLUDED_SOURCE_COLUMNS),
        excluded_internal_columns=POST_BOOKING_EXCLUDED_INTERNAL_COLUMNS,
    )
    for stage in (
        ModelStage.POST_BOOKING_DAY_1,
        ModelStage.POST_BOOKING_DAY_2,
        ModelStage.POST_BOOKING_DAY_3,
        ModelStage.POST_BOOKING_DAY_4,
    )
}

MODEL_STAGE_CONFIGS = {
    ModelStage.BOOKING_TIME: ModelStageConfig(
        stage=ModelStage.BOOKING_TIME,
        description="Booking-time no-show model that only uses fields available at reservation creation.",
        requires_snapshot_data=False,
        split_year_column="arrival_year",
        snapshot_day_offset=0,
        feature_policy=BOOKING_TIME_POLICY,
    ),
    ModelStage.POST_BOOKING_DAY_1: ModelStageConfig(
        stage=ModelStage.POST_BOOKING_DAY_1,
        description="Post-booking day 1 no-show model based on snapshot-safe as-of-cutoff fields.",
        requires_snapshot_data=True,
        split_year_column="snapshot_year",
        snapshot_day_offset=1,
        feature_policy=POST_BOOKING_FEATURE_POLICIES[ModelStage.POST_BOOKING_DAY_1],
    ),
    ModelStage.POST_BOOKING_DAY_2: ModelStageConfig(
        stage=ModelStage.POST_BOOKING_DAY_2,
        description="Post-booking day 2 no-show model based on snapshot-safe as-of-cutoff fields.",
        requires_snapshot_data=True,
        split_year_column="snapshot_year",
        snapshot_day_offset=2,
        feature_policy=POST_BOOKING_FEATURE_POLICIES[ModelStage.POST_BOOKING_DAY_2],
    ),
    ModelStage.POST_BOOKING_DAY_3: ModelStageConfig(
        stage=ModelStage.POST_BOOKING_DAY_3,
        description="Post-booking day 3 no-show model based on snapshot-safe as-of-cutoff fields.",
        requires_snapshot_data=True,
        split_year_column="snapshot_year",
        snapshot_day_offset=3,
        feature_policy=POST_BOOKING_FEATURE_POLICIES[ModelStage.POST_BOOKING_DAY_3],
    ),
    ModelStage.POST_BOOKING_DAY_4: ModelStageConfig(
        stage=ModelStage.POST_BOOKING_DAY_4,
        description="Post-booking day 4 no-show model based on snapshot-safe as-of-cutoff fields.",
        requires_snapshot_data=True,
        split_year_column="snapshot_year",
        snapshot_day_offset=4,
        feature_policy=POST_BOOKING_FEATURE_POLICIES[ModelStage.POST_BOOKING_DAY_4],
    ),
}


def get_model_stage_config(stage: str | ModelStage) -> ModelStageConfig:
    stage_key = ModelStage(stage)
    return MODEL_STAGE_CONFIGS[stage_key]


def list_model_stage_names() -> tuple[str, ...]:
    return tuple(stage.value for stage in ModelStage)


def resolve_output_root(output_root: Path, stage_config: ModelStageConfig) -> Path:
    if stage_config.stage == ModelStage.BOOKING_TIME:
        return output_root
    return output_root / stage_config.stage.value


def ensure_snapshot_support(stage_config: ModelStageConfig, snapshot_path: Path | None) -> None:
    if stage_config.requires_snapshot_data and snapshot_path is None:
        raise ValueError(
            f"Model stage '{stage_config.stage.value}' requires a snapshot dataset. "
            "Pass --snapshot-path with a stage-aware snapshot CSV."
        )

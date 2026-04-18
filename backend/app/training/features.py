from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.training.constants import HIGH_SEASON_MONTHS, MONTH_NAME_TO_NUMBER, NULL_LIKE_VALUES, RAW_NUMERIC_COLUMNS, RESERVATION_KEY_COLUMN, SOURCE_FILE_TO_PROPERTY_ID
from app.training.schemas import DatasetBundle
from app.training.stages import (
    ModelStage,
    ModelStageConfig,
    SNAPSHOT_OPTIONAL_COLUMNS,
    SNAPSHOT_REQUIRED_COLUMNS,
    StageFeaturePolicy,
    get_model_stage_config,
)


def _unique_columns(columns: list[str]) -> list[str]:
    return list(dict.fromkeys(columns))


def _normalize_text_series(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip()
    return normalized.mask(normalized.isin(NULL_LIKE_VALUES), pd.NA)


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _derive_lead_time_bucket(series: pd.Series) -> pd.Series:
    bins = [-np.inf, 0, 3, 7, 14, 30, 90, 180, 365, np.inf]
    labels = [
        "same_day",
        "1_3_days",
        "4_7_days",
        "8_14_days",
        "15_30_days",
        "31_90_days",
        "91_180_days",
        "181_365_days",
        "365_plus",
    ]
    return pd.cut(series, bins=bins, labels=labels)


def _derive_optional_binary_flag(series: pd.Series) -> pd.Series:
    numeric = _to_numeric(series)
    return np.where(numeric.isna(), pd.NA, (numeric > 0).astype(int))


SAFE_MODELING_METADATA_COLUMNS = {
    RESERVATION_KEY_COLUMN,
    "source_file",
    "source_row_number",
    "arrival_date",
    "model_stage",
    "feature_set_version",
    "snapshot_stage",
    "snapshot_at",
    "snapshot_year",
}


def normalize_and_map_reservations(raw_df: pd.DataFrame, stage_config: ModelStageConfig) -> pd.DataFrame:
    clean_df = raw_df.copy()

    object_columns = clean_df.select_dtypes(include=["object", "string"]).columns.tolist()
    for column in object_columns:
        clean_df[column] = _normalize_text_series(clean_df[column])

    for column in RAW_NUMERIC_COLUMNS:
        clean_df[column] = _to_numeric(clean_df[column])

    clean_df["source_file"] = clean_df["source_file"].astype("string")
    clean_df[RESERVATION_KEY_COLUMN] = clean_df[RESERVATION_KEY_COLUMN].astype("string")
    clean_df["source_row_number"] = clean_df["source_row_number"].astype(int)
    clean_df["property_id"] = clean_df["source_file"].map(SOURCE_FILE_TO_PROPERTY_ID).fillna("UNKNOWN_PROPERTY")
    clean_df["model_stage"] = stage_config.stage.value

    clean_df["arrival_month_number"] = clean_df["ArrivalDateMonth"].map(MONTH_NAME_TO_NUMBER)
    clean_df["arrival_date"] = pd.to_datetime(
        {
            "year": clean_df["ArrivalDateYear"],
            "month": clean_df["arrival_month_number"],
            "day": clean_df["ArrivalDateDayOfMonth"],
        },
        errors="coerce",
    )
    clean_df["ReservationStatusDate"] = pd.to_datetime(clean_df["ReservationStatusDate"], errors="coerce")

    clean_df["reservation_status"] = clean_df["ReservationStatus"]
    clean_df["reservation_status_date"] = clean_df["ReservationStatusDate"].dt.date
    clean_df["is_canceled"] = clean_df["IsCanceled"].fillna(0).astype("Int64")
    clean_df["no_show_flag"] = np.where(
        clean_df["reservation_status"] == "No-Show",
        1,
        np.where(clean_df["reservation_status"] == "Check-Out", 0, pd.NA),
    )
    clean_df["excluded_from_training"] = ~clean_df["reservation_status"].isin(["No-Show", "Check-Out"])
    clean_df["exclusion_reason"] = np.where(
        clean_df["reservation_status"] == "Canceled",
        "canceled_status",
        np.where(clean_df["excluded_from_training"], "unsupported_status", pd.NA),
    )

    clean_df["lead_time_days"] = clean_df["LeadTime"]
    clean_df["arrival_year"] = clean_df["ArrivalDateYear"]
    clean_df["arrival_month_name"] = clean_df["ArrivalDateMonth"]
    clean_df["arrival_week_number"] = clean_df["ArrivalDateWeekNumber"]
    clean_df["arrival_day_of_month"] = clean_df["ArrivalDateDayOfMonth"]
    clean_df["weekend_nights"] = clean_df["StaysInWeekendNights"]
    clean_df["week_nights"] = clean_df["StaysInWeekNights"]
    clean_df["adults"] = clean_df["Adults"]
    clean_df["children"] = clean_df["Children"]
    clean_df["babies"] = clean_df["Babies"]
    clean_df["meal_plan"] = clean_df["Meal"]
    clean_df["country_code"] = clean_df["Country"]
    clean_df["market_segment"] = clean_df["MarketSegment"]
    clean_df["distribution_channel"] = clean_df["DistributionChannel"]
    clean_df["is_repeated_guest"] = clean_df["IsRepeatedGuest"]
    clean_df["previous_cancellations"] = clean_df["PreviousCancellations"]
    clean_df["previous_non_cancelled_bookings"] = clean_df["PreviousBookingsNotCanceled"]
    clean_df["reserved_room_type"] = clean_df["ReservedRoomType"]
    clean_df["assigned_room_type"] = clean_df["AssignedRoomType"]
    clean_df["booking_changes"] = clean_df["BookingChanges"]
    clean_df["deposit_type"] = clean_df["DepositType"]
    clean_df["agent_code"] = clean_df["Agent"]
    clean_df["company_code"] = clean_df["Company"]
    clean_df["days_in_waiting_list"] = clean_df["DaysInWaitingList"]
    clean_df["customer_type"] = clean_df["CustomerType"]
    clean_df["adr"] = clean_df["ADR"]
    clean_df["required_car_parking_spaces"] = clean_df["RequiredCarParkingSpaces"]
    clean_df["total_special_requests"] = clean_df["TotalOfSpecialRequests"]

    return clean_df


def normalize_snapshot_reservations(snapshot_df: pd.DataFrame, stage_config: ModelStageConfig) -> pd.DataFrame:
    missing_required_columns = sorted(set(SNAPSHOT_REQUIRED_COLUMNS).difference(snapshot_df.columns))
    if missing_required_columns:
        raise ValueError(
            f"Snapshot dataset for stage '{stage_config.stage.value}' is missing required columns: "
            f"{missing_required_columns}"
        )

    clean_df = snapshot_df.copy()
    for column in SNAPSHOT_OPTIONAL_COLUMNS:
        if column not in clean_df.columns:
            clean_df[column] = pd.NA

    object_columns = clean_df.select_dtypes(include=["object", "string"]).columns.tolist()
    for column in object_columns:
        clean_df[column] = _normalize_text_series(clean_df[column])

    numeric_columns = [
        "source_row_number",
        "lead_time_days",
        "arrival_year",
        "arrival_week_number",
        "arrival_day_of_month",
        "weekend_nights",
        "week_nights",
        "adults",
        "children",
        "babies",
        "is_repeated_guest",
        "previous_cancellations",
        "previous_non_cancelled_bookings",
        "adr",
        "required_car_parking_spaces",
        "total_special_requests",
        "days_since_booking",
        "days_to_arrival",
        "booking_changes_as_of_cutoff",
        "days_in_waiting_list_as_of_cutoff",
        "days_since_last_booking_change",
        "days_since_room_assignment",
    ]
    for column in numeric_columns:
        clean_df[column] = _to_numeric(clean_df[column])

    clean_df["source_file"] = clean_df["source_file"].astype("string")
    clean_df[RESERVATION_KEY_COLUMN] = clean_df[RESERVATION_KEY_COLUMN].astype("string")
    clean_df["source_row_number"] = clean_df["source_row_number"].astype(int)
    clean_df["arrival_date"] = pd.to_datetime(clean_df["arrival_date"], errors="coerce")
    clean_df["snapshot_at"] = pd.to_datetime(clean_df["snapshot_at"], errors="coerce", utc=True)
    clean_df["snapshot_year"] = clean_df["snapshot_at"].dt.year
    clean_df["snapshot_stage"] = clean_df["snapshot_stage"].astype("string")
    clean_df["is_active_at_snapshot"] = clean_df["is_active_at_snapshot"].map(
        {
            "1": True,
            "0": False,
            "true": True,
            "false": False,
            True: True,
            False: False,
        }
    )
    clean_df["is_active_at_snapshot"] = clean_df["is_active_at_snapshot"].fillna(False).astype(bool)
    clean_df["final_outcome"] = clean_df["final_outcome"].astype("string")
    clean_df["model_stage"] = stage_config.stage.value

    clean_df = clean_df.loc[clean_df["snapshot_stage"] == stage_config.stage.value].copy()
    if clean_df.empty:
        raise ValueError(f"Snapshot dataset does not contain rows for stage '{stage_config.stage.value}'.")

    clean_df["no_show_flag"] = np.where(
        clean_df["final_outcome"] == "No-Show",
        1,
        np.where(clean_df["final_outcome"] == "Check-Out", 0, pd.NA),
    )
    clean_df["excluded_from_training"] = (~clean_df["final_outcome"].isin(["No-Show", "Check-Out"])) | (
        ~clean_df["is_active_at_snapshot"]
    )
    clean_df["exclusion_reason"] = np.where(
        clean_df["final_outcome"] == "Canceled",
        "canceled_before_or_after_snapshot",
        np.where(~clean_df["is_active_at_snapshot"], "inactive_at_snapshot", pd.NA),
    )

    return clean_df


def build_feature_dataset(clean_df: pd.DataFrame, stage_config: ModelStageConfig) -> pd.DataFrame:
    feature_policy = stage_config.feature_policy
    feature_df = clean_df.copy()

    numeric_fill_zero_columns = [
        "weekend_nights",
        "week_nights",
        "adults",
        "children",
        "babies",
        "previous_cancellations",
        "previous_non_cancelled_bookings",
        "required_car_parking_spaces",
        "total_special_requests",
    ]
    for column in numeric_fill_zero_columns:
        if column in feature_df.columns:
            feature_df[column] = feature_df[column].fillna(0)

    feature_df["total_nights"] = feature_df["weekend_nights"] + feature_df["week_nights"]
    feature_df["total_guests"] = feature_df["adults"].fillna(0) + feature_df["children"].fillna(0) + feature_df["babies"].fillna(0)
    feature_df["has_children"] = ((feature_df["children"].fillna(0) + feature_df["babies"].fillna(0)) > 0).astype(int)
    feature_df["is_family"] = (feature_df["total_guests"] >= 3).astype(int)
    feature_df["lead_time_bucket"] = _derive_lead_time_bucket(feature_df["lead_time_days"]).astype("string")
    feature_df["has_agent"] = feature_df["agent_code"].notna().astype(int)
    feature_df["has_company"] = feature_df["company_code"].notna().astype(int)
    feature_df["special_request_flag"] = (feature_df["total_special_requests"] > 0).astype(int)
    feature_df["adr_per_guest"] = feature_df["adr"] / feature_df["total_guests"].clip(lower=1)
    feature_df["adr_per_night_proxy"] = feature_df["adr"] / feature_df["total_nights"].clip(lower=1)
    feature_df["is_high_season"] = feature_df["arrival_month_name"].isin(HIGH_SEASON_MONTHS).astype(int)
    feature_df["is_weekend_heavy"] = (feature_df["weekend_nights"] > feature_df["week_nights"]).astype(int)
    feature_df["previous_cancel_ratio"] = feature_df["previous_cancellations"] / (
        feature_df["previous_cancellations"] + feature_df["previous_non_cancelled_bookings"] + 1
    )

    if stage_config.requires_snapshot_data:
        feature_df["has_any_booking_change_as_of_cutoff"] = _derive_optional_binary_flag(
            feature_df["booking_changes_as_of_cutoff"]
        )
        feature_df["waiting_list_flag_as_of_cutoff"] = _derive_optional_binary_flag(
            feature_df["days_in_waiting_list_as_of_cutoff"]
        )
        feature_df["room_assigned_flag_as_of_cutoff"] = np.where(
            feature_df["assigned_room_type_as_of_cutoff"].isna(),
            pd.NA,
            feature_df["assigned_room_type_as_of_cutoff"].notna().astype(int),
        )

    feature_df["feature_set_version"] = feature_policy.feature_set_version

    numeric_columns = feature_df.select_dtypes(include=[np.number]).columns
    feature_df.loc[:, numeric_columns] = feature_df.loc[:, numeric_columns].replace([np.inf, -np.inf], np.nan)

    feature_columns = _unique_columns(
        [
            RESERVATION_KEY_COLUMN,
            "source_file",
            "source_row_number",
            "property_id",
            "model_stage",
            "feature_set_version",
        ]
        + list(feature_policy.model_feature_columns)
        + [
            "arrival_date",
            "excluded_from_training",
            "exclusion_reason",
            "no_show_flag",
            "arrival_year",
        ]
    )
    for optional_metadata_column in ("snapshot_stage", "snapshot_at", "snapshot_year", "days_since_booking", "days_to_arrival"):
        if optional_metadata_column in feature_df.columns:
            feature_columns.append(optional_metadata_column)

    return feature_df[_unique_columns(feature_columns)].copy()


def enforce_feature_policy(modeling_df: pd.DataFrame, feature_policy: StageFeaturePolicy) -> None:
    metadata_columns = {
        column for column in SAFE_MODELING_METADATA_COLUMNS if column not in set(feature_policy.model_feature_columns)
    }
    columns_to_validate = [
        column for column in modeling_df.columns if column != "no_show_flag" and column not in metadata_columns
    ]

    present_internal_exclusions = sorted(set(feature_policy.excluded_internal_columns).intersection(columns_to_validate))
    if present_internal_exclusions:
        raise ValueError(f"Leakage-prone internal columns found in modeling frame: {present_internal_exclusions}")

    present_source_exclusions = sorted(set(feature_policy.excluded_source_columns).intersection(columns_to_validate))
    if present_source_exclusions:
        raise ValueError(f"Leakage-prone source columns found in modeling frame: {present_source_exclusions}")

    missing_expected = sorted(set(feature_policy.model_feature_columns).difference(columns_to_validate))
    if missing_expected:
        raise ValueError(f"Expected feature columns are missing: {missing_expected}")


def prepare_modeling_dataset(feature_df: pd.DataFrame, stage_config: ModelStageConfig) -> pd.DataFrame:
    feature_policy = stage_config.feature_policy
    modeling_df = feature_df.loc[~feature_df["excluded_from_training"]].copy()
    modeling_df["no_show_flag"] = modeling_df["no_show_flag"].astype(int)

    metadata_columns = [
        RESERVATION_KEY_COLUMN,
        "source_file",
        "source_row_number",
        "arrival_date",
        "model_stage",
        "feature_set_version",
        stage_config.split_year_column,
        "no_show_flag",
    ]
    for optional_metadata_column in ("snapshot_stage", "snapshot_at", "days_since_booking", "days_to_arrival"):
        if optional_metadata_column in modeling_df.columns:
            metadata_columns.append(optional_metadata_column)

    modeling_columns = _unique_columns(metadata_columns + list(feature_policy.model_feature_columns))
    modeling_df = modeling_df[modeling_columns].copy()
    enforce_feature_policy(modeling_df, feature_policy)
    return modeling_df


def _build_booking_time_bundle(raw_df: pd.DataFrame, stage_config: ModelStageConfig) -> DatasetBundle:
    clean_df = normalize_and_map_reservations(raw_df, stage_config)
    feature_df = build_feature_dataset(clean_df, stage_config)
    modeling_df = prepare_modeling_dataset(feature_df, stage_config)

    status_counts = clean_df["reservation_status"].fillna("MISSING").value_counts(dropna=False).to_dict()
    training_rows = int((~clean_df["excluded_from_training"]).sum())
    excluded_rows = int(clean_df["excluded_from_training"].sum())
    class_distribution = modeling_df["no_show_flag"].value_counts().sort_index().to_dict()

    import_summary: dict[str, Any] = {
        "model_stage": stage_config.stage.value,
        "row_count_raw": int(len(raw_df)),
        "row_count_clean": int(len(clean_df)),
        "row_count_training": training_rows,
        "row_count_excluded": excluded_rows,
        "status_distribution": status_counts,
        "class_distribution": class_distribution,
        "feature_policy": stage_config.feature_policy.to_machine_readable_dict(),
    }

    return DatasetBundle(
        raw_df=raw_df,
        clean_df=clean_df,
        feature_df=feature_df,
        modeling_df=modeling_df,
        import_summary=import_summary,
        stage_config=stage_config,
    )


def _build_snapshot_stage_bundle(snapshot_df: pd.DataFrame, stage_config: ModelStageConfig) -> DatasetBundle:
    clean_df = normalize_snapshot_reservations(snapshot_df, stage_config)
    feature_df = build_feature_dataset(clean_df, stage_config)
    modeling_df = prepare_modeling_dataset(feature_df, stage_config)

    status_counts = clean_df["final_outcome"].fillna("MISSING").value_counts(dropna=False).to_dict()
    training_rows = int((~clean_df["excluded_from_training"]).sum())
    excluded_rows = int(clean_df["excluded_from_training"].sum())
    class_distribution = modeling_df["no_show_flag"].value_counts().sort_index().to_dict()

    import_summary: dict[str, Any] = {
        "model_stage": stage_config.stage.value,
        "row_count_raw": int(len(snapshot_df)),
        "row_count_clean": int(len(clean_df)),
        "row_count_training": training_rows,
        "row_count_excluded": excluded_rows,
        "status_distribution": status_counts,
        "class_distribution": class_distribution,
        "feature_policy": stage_config.feature_policy.to_machine_readable_dict(),
        "split_year_column": stage_config.split_year_column,
    }

    return DatasetBundle(
        raw_df=snapshot_df,
        clean_df=clean_df,
        feature_df=feature_df,
        modeling_df=modeling_df,
        import_summary=import_summary,
        stage_config=stage_config,
    )


def build_dataset_bundle(source_df: pd.DataFrame, *, model_stage: str | ModelStage = ModelStage.BOOKING_TIME) -> DatasetBundle:
    stage_config = get_model_stage_config(model_stage)
    if stage_config.requires_snapshot_data:
        return _build_snapshot_stage_bundle(source_df, stage_config)
    return _build_booking_time_bundle(source_df, stage_config)

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_ARTIFACTS_ROOT = PROJECT_ROOT / "backend" / "artifacts" / "booking_time_no_show"

RAW_DATA_URLS = {
    "H1.csv": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-02-11/H1.csv",
    "H2.csv": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-02-11/H2.csv",
}

SOURCE_FILE_TO_PROPERTY_ID = {
    "H1.csv": "RESORT_H1",
    "H2.csv": "CITY_H2",
}

NULL_LIKE_VALUES = {
    "",
    "NULL",
    "null",
    "None",
    "none",
    "NA",
    "N/A",
    "nan",
    "NaN",
}

MONTH_NAME_TO_NUMBER = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

RAW_NUMERIC_COLUMNS = [
    "IsCanceled",
    "LeadTime",
    "ArrivalDateYear",
    "ArrivalDateWeekNumber",
    "ArrivalDateDayOfMonth",
    "StaysInWeekendNights",
    "StaysInWeekNights",
    "Adults",
    "Children",
    "Babies",
    "IsRepeatedGuest",
    "PreviousCancellations",
    "PreviousBookingsNotCanceled",
    "BookingChanges",
    "DaysInWaitingList",
    "ADR",
    "RequiredCarParkingSpaces",
    "TotalOfSpecialRequests",
]

EXCLUDED_SOURCE_COLUMNS = [
    "ReservationStatus",
    "ReservationStatusDate",
    "IsCanceled",
    "BookingChanges",
    "DaysInWaitingList",
    "AssignedRoomType",
]

EXCLUDED_INTERNAL_COLUMNS = [
    "reservation_status",
    "reservation_status_date",
    "is_canceled",
    "booking_changes",
    "days_in_waiting_list",
    "assigned_room_type",
    "no_show_flag",
]

FEATURE_SET_VERSION = "booking_time_v1"
ACTION_THRESHOLD = 0.35
HIGH_RISK_THRESHOLD = 0.50
TRAIN_YEARS = (2015, 2016)
TEST_YEARS = (2017,)
THRESHOLDS = (0.10, 0.20, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70)
TOP_K_VALUES = (25, 50, 100)
TOP_PERCENT_VALUES = (0.05, 0.10)
CALIBRATION_BIN_COUNT = 10

# Bootstrap assumption: July and August are the clearest peak-season months
# across the public H1/H2 dataset.
HIGH_SEASON_MONTHS = {"July", "August"}

BASE_MODEL_FEATURE_COLUMNS = [
    "property_id",
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
    "customer_type",
    "adr",
    "required_car_parking_spaces",
    "total_special_requests",
]

ENGINEERED_FEATURE_COLUMNS = [
    "total_nights",
    "total_guests",
    "has_children",
    "is_family",
    "lead_time_bucket",
    "has_agent",
    "has_company",
    "special_request_flag",
    "adr_per_guest",
    "adr_per_night_proxy",
    "is_high_season",
    "is_weekend_heavy",
    "previous_cancel_ratio",
]

MODEL_FEATURE_COLUMNS = BASE_MODEL_FEATURE_COLUMNS + ENGINEERED_FEATURE_COLUMNS

NUMERIC_FEATURE_COLUMNS = [
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
    "total_nights",
    "total_guests",
    "has_children",
    "is_family",
    "has_agent",
    "has_company",
    "special_request_flag",
    "adr_per_guest",
    "adr_per_night_proxy",
    "is_high_season",
    "is_weekend_heavy",
    "previous_cancel_ratio",
]

CATEGORICAL_FEATURE_COLUMNS = [
    "property_id",
    "arrival_month_name",
    "meal_plan",
    "country_code",
    "market_segment",
    "distribution_channel",
    "reserved_room_type",
    "deposit_type",
    "customer_type",
    "lead_time_bucket",
]

TARGET_COLUMN = "no_show_flag"
RESERVATION_KEY_COLUMN = "reservation_key"

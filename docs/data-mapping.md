# Data Mapping

## Purpose

This document explains how the current CSV files are interpreted inside the no-show system. It keeps ingestion, cleaning, feature building, and model training aligned.

The local proof-of-concept data comes from:

- `H1.csv`
- `H2.csv`

Both files use the same 31-column public hotel booking demand structure.

## Raw Data Notes

The CSVs are useful, but they are not clean application data. The import pipeline must handle:

- right-padded string values
- null-like placeholders such as `"NULL"`
- numeric-looking identifiers stored as padded strings
- sparse categories and high-cardinality ID-like fields

Do not train directly on raw strings. Normalize first, while preserving enough source context for traceability.

Recommended normalization:

- trim whitespace
- convert null-like placeholders to real missing values
- preserve raw values in the raw layer
- create clean normalized columns for modeling

## Modeling Objective

This project is a no-show model, not a generic cancellation model.

The target is:

- `no_show_flag = 1` for `ReservationStatus == "No-Show"`
- `no_show_flag = 0` for `ReservationStatus == "Check-Out"`

Rows with `ReservationStatus == "Canceled"` are excluded from the no-show training dataset.

Cancellation can be modeled later if the product needs it, but it should remain a separate outcome.

## Internal Layers

### 1. Raw Import Layer

Purpose:

- preserve imported rows close to the source files
- support traceability and reprocessing

Suggested table / object:

- `reservations_raw`

### 2. Clean Reservation Layer

Purpose:

- normalize types
- normalize categories
- create canonical reservation fields

Suggested table / object:

- `reservations_clean`

### 3. Feature Layer

Purpose:

- derive model features
- enforce exclusion rules
- keep train and inference transforms reproducible

Suggested table / object:

- `reservation_features`

### 4. Prediction Layer

Purpose:

- store scores, risk classes, thresholds, and model versions

Suggested table / object:

- `predictions`

### 5. Operational Event Layer

Purpose:

- provide real timestamped signals for post-booking scoring
- replace the synthetic proxies used in the proof-of-concept

Expected sources:

- payment attempts
- guest contact history
- campaign exposure
- guarantee / deposit workflow
- reservation change events

## Column Guidance

### Important Target-Related Columns

- `ReservationStatus` -> source for target construction; not a feature
- `ReservationStatusDate` -> metadata / analysis only; not a feature
- `IsCanceled` -> not a feature for the no-show model

### Strong Candidate Predictors

- `LeadTime`
- `ArrivalDateYear`
- `ArrivalDateMonth`
- `ArrivalDateWeekNumber`
- `ArrivalDateDayOfMonth`
- `StaysInWeekendNights`
- `StaysInWeekNights`
- `Adults`
- `Children`
- `Babies`
- `Meal`
- `Country`
- `MarketSegment`
- `DistributionChannel`
- `IsRepeatedGuest`
- `PreviousCancellations`
- `PreviousBookingsNotCanceled`
- `ReservedRoomType`
- `DepositType`
- `Agent`
- `Company`
- `CustomerType`
- `ADR`
- `RequiredCarParkingSpaces`
- `TotalOfSpecialRequests`

### Later-Stage-Only Predictors

- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

These are safe only when represented as timestamped as-of snapshot fields. Final-state values must not be used for earlier scoring cutoffs.

### Operational Signal Predictors

The architecture expects these signal families:

- customer identity
- payment failure
- communication history
- last-minute behavior
- channel campaign pressure
- guarantee / deposit detail

In H1/H2 these are synthetic proxies. In production they must come from timestamped operational systems.

## Internal Schema Mapping Suggestions

These names do not have to be the final production schema, but they should stay stable for the proof-of-concept.

| Internal field | Suggested source |
|---|---|
| `property_id` | derived from hotel source or file source |
| `source_file` | H1.csv / H2.csv |
| `lead_time_days` | `LeadTime` |
| `arrival_year` | `ArrivalDateYear` |
| `arrival_month_name` | `ArrivalDateMonth` |
| `arrival_week_number` | `ArrivalDateWeekNumber` |
| `arrival_day_of_month` | `ArrivalDateDayOfMonth` |
| `weekend_nights` | `StaysInWeekendNights` |
| `week_nights` | `StaysInWeekNights` |
| `adults` | `Adults` |
| `children` | `Children` |
| `babies` | `Babies` |
| `meal_plan` | `Meal` |
| `country_code` | `Country` |
| `market_segment` | `MarketSegment` |
| `distribution_channel` | `DistributionChannel` |
| `is_repeated_guest` | `IsRepeatedGuest` |
| `previous_cancellations` | `PreviousCancellations` |
| `previous_non_cancelled_bookings` | `PreviousBookingsNotCanceled` |
| `reserved_room_type` | `ReservedRoomType` |
| `deposit_type` | `DepositType` |
| `agent_code` | cleaned `Agent` |
| `company_code` | cleaned `Company` |
| `customer_type` | `CustomerType` |
| `adr` | `ADR` |
| `required_car_parking_spaces` | `RequiredCarParkingSpaces` |
| `total_special_requests` | `TotalOfSpecialRequests` |
| `no_show_flag` | derived from `ReservationStatus` |

## Import Requirements

Import code must:

1. preserve raw data
2. normalize text fields
3. log import batches
4. support reproducible re-runs
5. keep target construction separate from feature generation
6. document dropped rows and exclusion reasons

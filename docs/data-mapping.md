# Data Mapping

## Purpose
This file explains how the current CSV structure should be interpreted and mapped into the internal no-show system.

The current local dataset comes from two files:
- `H1.csv`
- `H2.csv`

They share the same 31-column structure.

---

## Raw data notes
Observed issues that the import pipeline must handle:

- many string values contain right-padded whitespace
- some null-like values are represented as string placeholders such as `"NULL"`
- some numeric-looking identifiers are stored as strings with padding
- there may be sparse categories and high-cardinality ID-like fields

Do not model directly on raw strings without normalization.

Recommended normalization:
- trim whitespace
- convert null-like placeholders to real missing values
- preserve the raw value in raw storage if needed
- create clean normalized columns for modeling

---

## Modeling objective
This project is not a generic cancellation model.

The no-show modeling target is:
- `no_show_flag = 1` for `ReservationStatus == "No-Show"`
- `no_show_flag = 0` for `ReservationStatus == "Check-Out"`

Rows with:
- `ReservationStatus == "Canceled"`

should be excluded from the no-show training dataset.

Canceled can be modeled later as a separate target if the product needs cancellation prediction.

---

## Suggested internal layers

### 1. Raw import layer
Example purpose:
- preserve imported rows as close to source as possible
- support traceability and reprocessing

Suggested table / object:
- `reservations_raw`

### 2. Clean reservation layer
Example purpose:
- normalize types
- normalize categories
- create canonical booking-time fields

Suggested table / object:
- `reservations_clean`

### 3. Feature layer
Example purpose:
- derive model features
- enforce exclusion rules
- support reproducible train/inference transforms

Suggested table / object:
- `reservation_features`

### 4. Prediction layer
Example purpose:
- persist score outputs and model versions

Suggested table / object:
- `predictions`

### 5. Operational event layer
Example purpose:
- provide real timestamped signals for post-booking scoring
- replace synthetic proxy features used in the proof-of-concept

Suggested sources:
- payment attempts
- guest contact history
- campaign exposure
- guarantee / deposit workflow
- reservation change events

---

## Column guidance

### Important target-related columns
- `ReservationStatus` -> source for target construction; not a feature
- `ReservationStatusDate` -> metadata / analysis only; not a feature
- `IsCanceled` -> do not use as a feature for the no-show model

### Strong candidate predictors
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

### Candidate later-stage-only predictors
- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

These fields are safe only when represented as as-of snapshot fields. Final-state values must not be used for earlier scoring cutoffs.

### Operational signal predictors
Current architecture expects these signal families:

- customer identity
- payment failure
- communication history
- last-minute behavior
- channel campaign pressure
- guarantee / deposit detail

In the public H1/H2 dataset these are synthetic proxies. In production they must come from timestamped operational systems.

---

## Internal schema mapping suggestions
These do not need to exactly match the final production schema, but they should be stable enough for the proof of concept.

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

---

## Import requirements
Import code must:
1. preserve raw data
2. normalize text fields
3. log import batches
4. support reproducible re-runs
5. clearly separate target construction from feature generation
6. document any dropped rows and why they were dropped

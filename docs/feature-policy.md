# Feature Policy

## Purpose

This document defines which features are allowed for staged no-show prediction and which fields are blocked because they leak the outcome or are not available at scoring time.

## Hard Exclusions

Never use these as model features:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- `no_show_flag`

These fields either encode the target directly or reveal final outcome state.

## Active Stages

### `customer_pre_reservation`

Question:

> Before a specific reservation is finalized, does this customer profile look likely to no-show?

Allowed feature groups:

- customer identity bucket
- historical booking depth
- previous cancellation / non-cancellation history
- payment failure history
- prior communication counts
- contact response score
- channel / campaign family
- campaign exposure and discount pressure
- guarantee / deposit strength

Do not include reservation-specific fields that are unknown before the reservation exists.

### `reservation_post_booking`

Question:

> After the reservation exists, does this specific reservation look likely to no-show?

Allowed feature groups:

- booking-time reservation fields
- customer-level signals
- payment retry / failure signals after booking
- guest message and response delay signals
- confirmation contact result
- last-minute and late-night behavior
- active campaign pressure
- guarantee / deposit verification status
- days to arrival at scoring

## Synthetic Signal Caveat

The public H1/H2 dataset does not contain real CRM, payment, messaging, campaign, or deposit event logs.

The current operational signals are synthetic proxies. They let the team validate the system design, feature contracts, API surface, and UI workflow before real event data is available. In production, these fields must be replaced by timestamped source data from:

- customer master data
- PMS reservation event history
- payment attempt logs
- CRM / messaging events
- campaign exposure logs
- deposit and guarantee workflows

Synthetic signals must be marked as synthetic in model documentation and must not be presented as proven production predictors.

## Booking-Time Compatibility Policy

The legacy `booking_time` stage remains leakage-safe and may use:

- hotel / property id
- lead time
- arrival calendar fields
- stay length
- guest counts
- meal plan
- country
- market segment
- distribution channel
- repeated guest flag
- previous cancellations
- previous non-canceled bookings
- reserved room type
- deposit type
- customer type
- ADR
- parking requirement
- special request count, with timing caution

Excluded from booking-time:

- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

These fields may be created or updated after booking, so final-state values are not safe for a booking-time model.

## Snapshot Stages

`post_booking_day_1` through `post_booking_day_4` require as-of snapshot data.

Allowed only if timestamped and known at cutoff:

- `booking_changes_as_of_cutoff`
- `days_in_waiting_list_as_of_cutoff`
- `assigned_room_type_as_of_cutoff`
- `days_since_last_booking_change`
- `days_since_room_assignment`

Final-state versions of these fields are not acceptable for snapshot-stage training.

## Engineering Requirements

Feature code must:

1. centralize stage-specific feature lists
2. centralize excluded columns
3. fail loudly if leakage columns enter training
4. write final feature names to a machine-readable artifact
5. keep numeric and categorical feature lists explicit
6. distinguish real operational signals from synthetic proxies

# Dataset Card

## Dataset

The current proof-of-concept uses:

- `data/raw/H1.csv`
- `data/raw/H2.csv`

Both files follow the public hotel booking demand schema.

## Unit Of Observation

Each row represents one reservation record in the source extract.

## Target Construction

The no-show target is built from final reservation status:

- positive: `ReservationStatus == "No-Show"`
- negative: `ReservationStatus == "Check-Out"`

Rows with `ReservationStatus == "Canceled"` are excluded from no-show training.

Cancellation and no-show are different operational outcomes, so they should not be merged into one binary target.

## Known Data Limitations

The public CSV files are final-state extracts. They do not include full event history for:

- payment attempts
- customer contact attempts
- guest responses
- campaign exposures
- deposit verification
- reservation change timestamps
- room assignment timestamps

Because of that, H1/H2 alone cannot fully validate true post-booking as-of modeling.

## Synthetic Features

The project creates synthetic proxies for operational signals that would matter in a real hotel environment:

- customer identity
- payment failure
- communication history
- last-minute behavior
- channel campaign pressure
- guarantee / deposit detail

These proxies are useful for architecture validation, UI development, and pipeline testing. They should not be treated as production evidence.

## Excluded Fields

Hard exclusions:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`

Excluded unless available as timestamped as-of snapshots:

- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

## Split

Current temporal split:

- train: 2015, 2016
- test: 2017

Random split should not be used for headline results.

## Data Quality Requirements

Ingestion must:

- preserve raw rows
- trim padded strings
- normalize null-like placeholders
- keep target construction separate from feature generation
- log dropped rows and exclusion reasons
- make feature columns reproducible

## Production Data Needed

Before production use, connect timestamped sources for:

- PMS reservation events
- payment gateway attempts
- CRM and messaging history
- campaign exposure logs
- deposit and guarantee workflow states
- action outcomes from operations

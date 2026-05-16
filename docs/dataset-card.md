# Dataset Card

## Dataset

Current proof-of-concept data:

- `data/raw/H1.csv`
- `data/raw/H2.csv`

Source files share the public hotel booking demand schema.

## Unit Of Observation

One row represents one hotel reservation record in the source extract.

## Target Construction

No-show target:

- positive: `ReservationStatus == "No-Show"`
- negative: `ReservationStatus == "Check-Out"`

Excluded:

- `ReservationStatus == "Canceled"`

Reason:

- cancellation and no-show are different operational outcomes

## Known Data Limitations

The public CSV files are final-state extracts. They do not provide complete event history for:

- payment attempts
- customer contact attempts
- guest responses
- campaign exposures
- deposit verification
- reservation change timestamps
- room assignment timestamps

Because of this, real post-booking as-of modeling cannot be fully validated with H1/H2 alone.

## Synthetic Features

The project currently creates synthetic proxies for strong operational signals:

- customer identity
- payment failure
- communication history
- last-minute behavior
- channel campaign pressure
- guarantee / deposit detail

These are acceptable for architecture validation, UI development, and pipeline testing. They are not enough for a production evidence claim.

## Excluded Fields

Hard exclusions:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`

Excluded unless available as as-of snapshot:

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

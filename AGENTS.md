# AGENTS.md

## Project
This repository implements an internal **Hotel Chain No-Show Prediction System**.

The goal is to:
- import hotel booking data
- build a clean internal reservation model
- generate no-show risk scores
- expose risk review APIs
- support an operations dashboard
- store audit trails for human actions
- report model and business metrics

The current proof-of-concept dataset is based on the public Hotel Booking Demand structure and the local files `H1.csv` and `H2.csv`.

---

## Source of truth
Use these files as the primary context, in this order:

1. `docs/modeling-plan.md`
2. `docs/feature-policy.md`
3. `docs/data-mapping.md`
4. `docs/acceptance-criteria.md`
5. `docs/backlog.md`
6. `PLANS.md`

If there is a conflict:
- `docs/modeling-plan.md` wins for modeling decisions
- `docs/feature-policy.md` wins for leakage and feature-availability decisions
- `docs/acceptance-criteria.md` wins for delivery and verification decisions

Do **not** invent business rules that are not justified by these files.

---

## Product scope
Core modules:
1. Reservation import
2. Feature building
3. Baseline no-show model training
4. Batch scoring / prediction persistence
5. Risk review API
6. Reservation action logging
7. Reporting
8. Internal dashboard
9. Authentication / authorization scaffolding
10. Containerized local development

---

## Current modeling objective
The initial objective is **binary no-show prediction**, not generic cancellation prediction.

### Initial target definition
Build `no_show_flag` as:

- `1` if `ReservationStatus == "No-Show"`
- `0` if `ReservationStatus == "Check-Out"`

For the first model:
- exclude rows where `ReservationStatus == "Canceled"`

Do not use `ReservationStatus`, `ReservationStatusDate`, or `IsCanceled` as model features.

---

## Time-of-prediction policy
The primary model for the first release is a **booking-time model**.

That means:
- only use data that is truly available at booking time
- reject features that depend on later operational events
- if a feature is only known later, move it to a future pre-arrival model, not the first model

There may later be a second model:
- `pre_arrival_model` (for T-7 / T-2 style scoring)

Do not mix these two feature policies.

---

## Tech stack
Preferred stack unless the repo already defines otherwise:

- Backend: FastAPI
- Frontend: Next.js
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Training / data work: Python
- Tests: pytest
- Containerization: Docker + docker compose

If the repository already contains a different stack, adapt carefully instead of force-replacing it.

---

## Architecture rules
Use a layered structure:

- `api/`
- `services/`
- `repositories/`
- `models/`
- `schemas/`
- `jobs/`
- `db/`

Rules:
- keep business logic out of route handlers
- keep SQL / ORM logic out of UI and route handlers
- isolate training code from API code
- isolate feature-building code from raw CSV ingestion
- make model artifacts replaceable
- use explicit schemas for request / response boundaries

---

## Data rules
Treat raw imported data and clean modeling data separately.

Recommended layers:
- raw import table(s)
- cleaned reservation table
- feature table / materialized feature dataset
- predictions table
- action / audit tables

Never destroy raw source columns during import.
Preserve traceability from raw row -> cleaned row -> feature row -> prediction.

The local CSV files contain padded strings and string placeholders like `"NULL"` in some fields.
Trim and normalize text carefully before modeling.

---

## Feature rules
Follow `docs/feature-policy.md`.

### Safe core derived features for the booking-time model
These are expected to be implemented unless they create technical issues:

- `TotalNights = StaysInWeekendNights + StaysInWeekNights`
- `TotalGuests = Adults + Children + Babies`
- `HasChildren = 1 if Children + Babies > 0 else 0`
- `IsFamily = 1 if TotalGuests >= 3 else 0`
- `LeadTimeBucket`
- `HasAgent`
- `HasCompany`
- `SpecialRequestFlag` only if policy in `docs/feature-policy.md` allows it
- `ADRPerGuest = ADR / max(TotalGuests, 1)`
- `ADRPerNightProxy`
- `IsHighSeason`
- `IsWeekendHeavy = 1 if weekend_nights > week_nights else 0`
- `PreviousCancelRatio = PreviousCancellations / (PreviousCancellations + PreviousBookingsNotCanceled + 1)`

### Explicitly disallowed for the first model
Do not use:
- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

These are excluded from the first booking-time model because they create leakage or time-of-availability violations.

---

## Model rules
Start simple and compare models.

Required sequence:
1. establish a trivial baseline
2. establish a linear/logistic baseline
3. train CatBoost as the first serious tabular model
4. compare with at least one alternative if time permits

### Why CatBoost is preferred early
The current dataset contains:
- many categorical features
- sparse fields
- missing values
- text-coded identifiers

CatBoost is a strong candidate because it handles categorical-heavy tabular data well with less encoding overhead.

### Metrics
Do not optimize for plain accuracy.
Primary metrics:
- PR-AUC
- Recall
- Precision
- F1
- confusion matrix
- threshold analysis

### Split strategy
Do not use naive random split by default.
Prefer a time-aware split:
- train on earlier years
- validate/test on later periods

Document any split assumptions.

### Class imbalance
The no-show class is rare.
Use:
- class weights
- threshold tuning
- metric-aware evaluation

Do not claim success using accuracy alone.

---

## Security and privacy
Treat the following as sensitive if they appear in future real hotel data:
- email
- phone number
- loyalty data
- personal identifiers
- payment-adjacent fields

Do not log secrets.
Do not expose internal admin routes without authorization.
Do not overexpose PII in API responses.

---

## Testing rules
For every meaningful feature or module:
- add tests
- include a happy path
- include at least one error or validation path
- include integration tests for critical flows when practical

Important:
- test that excluded leakage features are not accidentally used
- test that canceled reservations are excluded from first-model training
- test that prediction timestamps and model versions are persisted

---

## Done criteria
A task is complete only if:
1. code is implemented
2. tests are added or updated
3. docs are updated if assumptions changed
4. relevant checks pass
5. the task summary lists changed files, assumptions, and out-of-scope items

---

## Commands
Before finishing work, run the relevant commands if configured:

- backend tests
- model training smoke tests
- lint
- type checks
- build
- local API start check

---

## Output format
At the end of each task, provide:
1. what changed
2. which files changed
3. assumptions
4. risks / unresolved points
5. how to run and verify the result

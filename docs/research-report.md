# Research Report: Hotel No-Show Prediction and Operations Dashboard

## Abstract

This project implements an end-to-end hotel no-show prediction system that connects supervised tabular ML to operational decision support. The system includes leakage-safe feature engineering, temporal validation, calibrated risk scoring, threshold and Top-K evaluation, prediction persistence, artifact fallback views, a FastAPI backend, PostgreSQL schema, and a Next.js operations dashboard.

The current proof-of-concept uses public hotel booking data and synthetic operational signal proxies. The architecture is designed so those proxies can later be replaced with timestamped production signals from PMS, CRM, payment, campaign, and action outcome systems.

## Motivation

Hotel no-shows create unused room capacity, staffing inefficiency, and revenue risk. A model is useful only if it becomes part of a real operational workflow: a queue, a threshold policy, clear score semantics, and monitoring that shows whether the actions are working.

For that reason, this project evaluates the model as an operations system, not as a standalone notebook classifier.

## Task Definition

The binary target is:

- `1`: final reservation status is `No-Show`
- `0`: final reservation status is `Check-Out`

Reservations with final status `Canceled` are excluded from no-show training because cancellation is a different operational outcome.

The active stages are:

- `customer_pre_reservation`: customer-level no-show propensity before a specific reservation is finalized
- `reservation_post_booking`: reservation-level no-show risk after a booking exists

## Data

The proof-of-concept uses the `H1.csv` and `H2.csv` hotel booking files.

Known limitations:

- the dataset is a final-state extract
- it does not contain full payment attempt logs
- it does not contain CRM or messaging event history
- it does not contain campaign exposure logs
- it does not contain guarantee/deposit workflow events
- it does not provide complete as-of snapshot histories for all post-booking fields

Because of these limitations, current operational signal families are represented as synthetic proxies. They validate architecture and workflow design, but they should not be treated as production evidence.

## Leakage Controls

Hard exclusions:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- `no_show_flag`

Additional rule:

- final-state operational fields cannot be used for earlier scoring cutoffs unless represented as timestamped as-of features

Canceled rows are excluded from no-show training.

## Modeling Approach

The active model is:

- `catboost_with_logistic_score`

Model flow:

1. Build stage-specific features.
2. Train a Logistic Regression feeder.
3. Generate `logistic_regression_score`.
4. Feed that score into CatBoost.
5. Calibrate CatBoost probabilities with isotonic regression.
6. Write model, prediction, and evaluation artifacts.

Logistic Regression is not a separate product candidate. It is an internal feeder signal.

## Validation

Evaluation uses a temporal split:

- train: 2015-2016
- test: 2017

Random split is avoided for headline quality claims because production scoring predicts future reservations from past observations.

## Metrics

Training reports include:

- PR-AUC
- ROC-AUC
- precision at threshold
- recall at threshold
- F1 at threshold
- actioned count
- recall at Top-K
- Brier score
- calibration table
- feature percentile summary
- feature drift summary

Metric values are generated after each training run and stored in stage-specific artifact directories. This report does not hard-code metric values because they depend on the latest training run and configuration.

## Operational Threshold Policy

Scores represent direct no-show probability.

Current threshold policy:

- action threshold: `0.90`
- high risk: `>= 0.80`
- medium risk: `>= 0.67`
- notable risk: `>= 0.50`
- low risk: `< 0.50`

Threshold changes do not require retraining, but they should be reviewed using precision, recall, and action volume.

## System Design

Backend:

- FastAPI routes
- SQLAlchemy ORM models
- PostgreSQL persistence
- Alembic migration
- repository/service separation
- artifact readers for local fallback

Frontend:

- dashboard summary
- customer risk view
- reservation risk view
- reservation queue
- reservation detail and action workflow
- management reports

ML pipeline:

- ingestion
- cleaning
- target construction
- feature engineering
- temporal split
- training
- calibration
- evaluation
- artifact persistence
- optional database persistence

## Reproducibility

Reproducibility support:

- CLI training entrypoint
- stage-specific feature policies
- generated feature lists
- generated evaluation artifacts
- model card
- dataset card
- CI workflow
- backend tests
- frontend typecheck and production build

## Main Risks

- Synthetic operational features may overstate production readiness.
- Final-state data can cause leakage if reused without timestamp checks.
- Thresholds may create unrealistic action volume if not monitored.
- Calibration can drift by season, source market, channel, or campaign mix.
- Action effectiveness requires real outcome labels, not only action status.

## Next Work

1. Replace synthetic operational features with timestamped production data.
2. Add a dedicated scoring job separate from training.
3. Persist predictions to the database by default.
4. Add role-based access control.
5. Track action outcomes and measure intervention impact.
6. Add periodic drift and calibration monitoring.
7. Add period-over-period management reporting.

# ML System Guide

This guide replaces the previous separate modeling, feature, data, model-card, and evaluation documents. It is the current source of truth for the ML side of the project.

## Objective

The system predicts hotel reservations that may need follow-up before arrival. It supports two related but separate questions:

- pure no-show risk: will the guest fail to arrive without canceling?
- arrival failure risk: will the reservation fail to become a completed stay because it is canceled or no-show?

The main operational product uses `arrival_failure_post_booking`. The pure no-show stage remains available as a stricter technical view.

## Data

The proof-of-concept uses the public hotel booking demand files:

- `H1.csv`
- `H2.csv`

Each row is one reservation record. The files are final-state extracts, so they do not contain full event history for payment attempts, CRM messages, guest responses, campaign exposure, deposit verification, booking changes, or room assignment timing.

Because of this, some operational signals are synthetic proxies. They are useful for validating the architecture and UI, but they are not production evidence.

## Targets

Pure no-show target:

- positive: `ReservationStatus == "No-Show"`
- negative: `ReservationStatus == "Check-Out"`
- excluded: `ReservationStatus == "Canceled"`

Arrival failure target:

- positive: `ReservationStatus` in `Canceled`, `No-Show`
- negative: `ReservationStatus == "Check-Out"`

Canceled rows must not be mixed into the pure no-show target. They are included only in the arrival failure stage.

## Active Stages

- `customer_pre_reservation`: customer-level no-show propensity before a specific reservation is finalized
- `reservation_post_booking`: reservation-level pure no-show risk after booking
- `arrival_failure_post_booking`: reservation-level canceled-or-no-show risk after booking

Historical or optional stages:

- `booking_time`: retained for compatibility and leakage-safe baseline work
- `post_booking_day_1` through `post_booking_day_4`: require real as-of snapshot data before they can be trusted

## Leakage Policy

Never use these as model features:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- `no_show_flag`

For booking-time scoring, do not use final-state values from:

- `BookingChanges`
- `DaysInWaitingList`
- `AssignedRoomType`

Those fields are safe only if they are represented as timestamped as-of snapshot fields.

Feature code must centralize stage-specific feature lists, block leakage columns before training, and write final feature names to a machine-readable artifact.

## Feature Groups

Main allowed feature groups:

- booking and arrival context
- customer history
- payment failure signals
- communication signals
- campaign and channel signals
- guarantee and deposit signals
- days to arrival at scoring

In the public dataset, several of these groups are synthetic. In production, they must come from timestamped PMS, CRM, payment, messaging, campaign, and guarantee/deposit systems.

## Model Architecture

The active final model is:

- `catboost_with_logistic_score`

Model flow:

1. Build stage-specific features.
2. Block leakage columns.
3. Train a Logistic Regression feeder.
4. Generate out-of-fold feeder scores when feasible.
5. Add `logistic_regression_score` to CatBoost features.
6. Train CatBoost.
7. Generate out-of-fold CatBoost scores for calibration.
8. Fit isotonic calibration.
9. Score the temporal test split and write artifacts.

Logistic Regression is not shown as a separate production candidate. It is an internal feeder signal.

## Split And Evaluation

Random split is not used for headline quality claims.

Current temporal split:

- train: 2015 and 2016
- test: 2017

Primary outputs:

- PR-AUC
- ROC-AUC
- precision, recall, and F1 at threshold
- actioned count
- recall in fixed-size follow-up lists
- Brier score
- calibration table
- feature percentiles
- feature drift report
- threshold policy report
- stacking summary

Accuracy is not a decision metric here because pure no-show is a minority event and arrival failure still needs workload-aware threshold review.

## Threshold Policy

Scores are direct positive-class probabilities for the selected stage. Do not invert them.

Current policy:

- action threshold: `0.40`
- high risk: `>= 0.80`
- medium risk: `>= 0.67`
- notable risk: `>= 0.50`
- low risk: `< 0.50`

Thresholds can be changed without retraining, but precision, recall, action volume, and fixed-list capture should be reviewed after every training run.

## Artifacts

Active artifact locations:

- `backend/artifacts/booking_time_no_show/customer_pre_reservation/latest/`
- `backend/artifacts/booking_time_no_show/reservation_post_booking/latest/`
- `backend/artifacts/booking_time_no_show/arrival_failure_post_booking/latest/`

Typical outputs:

- `datasets/reservations_clean.csv`
- `datasets/reservation_features.csv`
- `models/catboost_with_logistic_score.cbm`
- `models/logistic_regression_feeder.joblib`
- `models/catboost_probability_calibrator.joblib`
- `predictions/catboost_with_logistic_score_predictions.csv`
- `reports/evaluation_summary.json`
- `reports/model_comparison.csv`
- `reports/*_threshold_metrics.csv`
- `reports/*_top_k_metrics.csv`
- `reports/*_calibration.csv`
- `reports/feature_percentiles.csv`
- `reports/feature_drift.csv`
- `reports/risk_thresholds.json`
- `reports/threshold_policy.json`
- `reports/stacking_summary.json`

## Model Selection Policy

The active candidate set intentionally contains one final model. More model families should not be added just to create a leaderboard.

CatBoost is the default because the data is tabular, categorical fields carry signal, missing values and sparse categories are expected, and feature interactions matter.

Future alternatives can be benchmarked only when there is a clear engineering reason. They must use the same temporal split, feature policy, target, threshold reporting, and calibration review.

Selection priority:

1. PR-AUC
2. recall in fixed-size follow-up lists
3. precision at action threshold
4. calibration and Brier score
5. ROC-AUC
6. production cost and maintainability

## Production Caveats

- The current dataset lacks real payment, contact, campaign, and deposit event logs.
- Synthetic signals can validate architecture, but they cannot prove production model quality.
- Arrival failure usually scores better than pure no-show because cancellations are more common.
- Real deployment needs timestamped source data and periodic drift/calibration monitoring.

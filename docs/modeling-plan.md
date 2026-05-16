# Modeling Plan

## Current Decision

This project is a staged no-show prediction system. It is not a cancellation model, and it is not a generic BI product.

Active production-style stages:

- `customer_pre_reservation`: customer-level no-show propensity before a specific reservation is finalized.
- `reservation_post_booking`: reservation-level no-show risk after booking, using operational signals.

Historical / optional stages:

- `booking_time`: retained for compatibility and leakage-safe baseline work.
- `post_booking_day_1` ... `post_booking_day_4`: require real as-of snapshot data before they can be trusted.

## Target

Binary target:

- `no_show_flag = 1` when final `ReservationStatus == "No-Show"`
- `no_show_flag = 0` when final `ReservationStatus == "Check-Out"`

Excluded from no-show training:

- `ReservationStatus == "Canceled"`

Canceled is a different business outcome. It should be modeled separately if the product needs cancellation prediction.

## Model Architecture

The active model candidate is:

- `catboost_with_logistic_score`

Logistic Regression is not a separate candidate. It is an internal feeder model:

- trained on the same stage feature policy
- used to produce `logistic_regression_score`
- fed into CatBoost as an additional feature
- generated out-of-fold for training when enough rows are available

CatBoost output is calibrated with isotonic regression using out-of-fold CatBoost scores.

This keeps the product focused on one final model while still giving CatBoost a stable linear baseline signal.

## Split Policy

Random split is not allowed for model quality claims.

Current temporal split:

- train: 2015, 2016
- test: 2017

Reason:

- production predicts future reservations from past reservation history
- random split would overstate quality when hotel, season, channel, and campaign patterns repeat

## Training Policy

Default stance:

- keep CatBoost as the only active final candidate
- use early stopping instead of large brute-force training
- tune only after the feature contract and calibration are stable
- compare by stage, not by a global leaderboard

Controlled tuning is allowed only when it records:

- stage
- split dates
- feature set version
- model parameters
- threshold policy
- calibration method
- Top-K and threshold metrics

## Threshold And Risk Semantics

Score means direct no-show probability. Do not invert it.

Current policy:

- `score >= 0.90`: action threshold
- `score >= 0.80`: high risk
- `score >= 0.67`: medium risk
- `score >= 0.50`: notable risk
- otherwise: low risk

Thresholds are operational decisions. They can be changed without retraining, but precision, recall, and action volume must be reviewed after every training run.

## Feature Policy

Binding document:

- `docs/feature-policy.md`

Hard leakage exclusions remain:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- direct final-state operational fields unless available at the scoring cutoff

Operational signals such as payment failure, contact history, campaign pressure, and guarantee/deposit status are synthetic proxies when using public H1/H2 data. In a real deployment they must come from PMS, CRM, payment, messaging, and campaign systems with event timestamps.

## Evaluation Priority

Primary quality view:

1. PR-AUC
2. Recall at Top-K
3. Precision at action threshold
4. Calibration / Brier score
5. ROC-AUC

Accuracy is not a decision metric here because no-show is a minority event.

## Minimum Acceptance

A trained stage is acceptable only if:

- temporal split is used
- leakage guard passes
- `catboost_with_logistic_score` trains end to end
- Logistic Regression feeder uses out-of-fold scores when feasible
- calibrated scores are reported
- threshold and Top-K tables are produced
- feature drift and feature percentiles are available for review
- score semantics remain direct no-show probability

## Production Caveats

The public dataset is final-state oriented. It does not contain real payment attempts, contact events, campaign exposure logs, or as-of room assignment history.

Therefore:

- current operational signals are useful for architecture and UI validation
- they are not a substitute for real operational event data
- post-booking models must be revalidated when real timestamped signals arrive

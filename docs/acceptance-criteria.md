# Acceptance Criteria

This document defines what "done" means for the no-show prediction system. A feature is not complete just because a screen renders or a model trains once; it needs to be reproducible, testable, and aligned with the project rules.

## General

A task is complete when:

- the requested behavior is implemented
- the changed behavior has tests or a clear validation path
- important assumptions are documented
- related documentation is updated when the behavior changes

## Data And Target

The data layer is ready when:

- `H1.csv` and `H2.csv` load reproducibly
- raw source rows are preserved
- clean reservation records are generated
- `no_show_flag` is derived correctly
- canceled reservations are excluded from no-show training
- target construction is covered by tests

## Feature Pipeline

The feature pipeline is ready when:

- feature lists are explicit for each stage
- leakage columns are blocked before training
- synthetic operational signals are documented clearly
- numeric and categorical feature lists are stable
- a machine-readable feature list artifact is written
- transformations can be reproduced from the same input data

## Model Training

Training is ready when:

- `customer_pre_reservation` trains end to end
- `reservation_post_booking` trains end to end
- the final candidate is `catboost_with_logistic_score`
- Logistic Regression is used only as a feeder score
- feeder scores are generated out-of-fold when enough rows exist
- CatBoost probabilities are calibrated
- the model, feeder, calibrator, metadata, and predictions are persisted

## Evaluation

Each training run should report:

- PR-AUC
- ROC-AUC
- threshold precision, recall, and F1
- actioned count
- Top-K recall
- calibration and Brier score
- selected action threshold
- risk bands
- feature drift and feature percentiles

## Product Surfaces

The product surface is ready when:

- `/customer-risk` shows the customer-level stage
- `/reservation-risk` shows the reservation-level stage
- `/dashboard` uses reservation-stage artifact fallback when DB predictions are absent
- `/reports` describes active model quality, not a broad benchmark exercise
- action thresholds and risk labels match backend constants

## Production Readiness Caveat

This proof-of-concept is not production-ready until synthetic operational signals are replaced with timestamped real source events and revalidated with the same temporal evaluation policy.

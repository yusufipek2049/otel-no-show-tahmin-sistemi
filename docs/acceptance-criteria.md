# Acceptance Criteria

## General

A task is not complete unless:

- implementation is present when requested
- tests or validation are run when behavior changes
- assumptions are documented
- affected docs are updated

## Data And Target

Done when:

- `H1.csv` and `H2.csv` load reproducibly
- raw data is preserved
- clean data is generated
- `no_show_flag` is derived correctly
- canceled rows are excluded from no-show training
- target construction is tested

## Feature Pipeline

Done when:

- stage-specific feature lists are explicit
- leakage columns are blocked
- synthetic operational signals are documented
- numeric and categorical feature lists are stable
- feature list artifact is written
- transformations are reproducible

## Model Training

Done when:

- `customer_pre_reservation` trains end to end
- `reservation_post_booking` trains end to end
- final candidate is `catboost_with_logistic_score`
- Logistic Regression is used only as feeder score
- feeder score is out-of-fold when enough data exists
- CatBoost probability calibration is applied
- model, feeder, calibrator, metadata, and predictions are persisted

## Evaluation

Done when:

- PR-AUC is reported
- ROC-AUC is reported
- threshold precision / recall / F1 are reported
- actioned count is reported
- Top-K recall is reported
- calibration and Brier score are reported
- selected action threshold is explicit
- risk bands are explicit
- feature drift and feature percentiles are available for review

## Product Surfaces

Done when:

- `/customer-risk` shows the customer-level stage
- `/reservation-risk` shows the reservation-level stage
- `/dashboard` uses the operational reservation-stage artifact fallback when DB predictions are absent
- `/reports` uses active model quality wording instead of multi-candidate benchmark wording
- action threshold and risk labels match backend constants

## Production Readiness Caveat

This proof-of-concept is not production-ready until synthetic operational signals are replaced with timestamped real source events and revalidated with the same temporal evaluation policy.

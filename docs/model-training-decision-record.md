# Model Training Decision Record

Status: accepted

Last updated: 2026-05-05

## Decision

Use two active no-show stages:

- `customer_pre_reservation`
- `reservation_post_booking`

Use one final model architecture:

- `catboost_with_logistic_score`

Logistic Regression is an internal feeder model, not a displayed candidate.

## Rationale

The decision follows standard ML engineering practice:

- start with a clear target and leakage policy
- use temporal validation for future-facing predictions
- document model and dataset assumptions explicitly
- tie threshold selection to operational capacity
- calibrate probability-like scores before relying on fixed thresholds
- monitor drift and data quality after training

Useful external references:

- Google Rules of ML: https://developers.google.com/machine-learning/guides/rules-of-ml/
- Model Cards: https://research.google/pubs/pub48120/
- Datasheets for Datasets: https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework

## Training Configuration

Current fixed policy:

- temporal split: train 2015-2016, test 2017
- action threshold: `0.90`
- threshold grid: `0.50`, `0.67`, `0.80`, `0.90`, `0.95`
- risk bands: high at `0.80`, medium at `0.67`, notable at `0.50`
- calibration: isotonic
- feeder cross-validation folds: 3
- operational action capacity reference: 50

## Model Flow

1. Build stage-specific features.
2. Block leakage columns.
3. Train the Logistic Regression feeder.
4. Generate out-of-fold feeder scores when feasible.
5. Add `logistic_regression_score` to CatBoost features.
6. Train CatBoost.
7. Generate out-of-fold CatBoost scores for calibration.
8. Fit the isotonic calibrator.
9. Score the test split and write artifacts.

## Go / No-Go Gates

Do not promote a run if:

- target construction changed without documentation
- canceled rows entered no-show training
- leakage columns entered the model matrix
- scores were inverted
- calibration is absent
- threshold action volume is operationally unrealistic
- feature drift is unexplained
- synthetic signals are treated as real production evidence

## Known Weaknesses

The current dataset does not contain real payment, contact, campaign, or deposit event logs. The architecture is stronger than the evidence currently available from H1/H2.

The next meaningful quality improvement should come from real operational data, not from adding more model families.

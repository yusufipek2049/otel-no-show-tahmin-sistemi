# Model Evaluation Plan

## Objective

Evaluation must answer two questions:

- Can the model rank likely no-shows above likely arrivals?
- At the chosen action threshold, is the operational workload worth the captured no-show volume?

This is a rare-event problem. Accuracy is not a useful decision metric.

## Evaluation Layers

### 1. Ranking Quality

Primary:

- PR-AUC

Secondary:

- ROC-AUC

PR-AUC is primary because no-show is the positive minority class.

### 2. Operational Utility

Report:

- precision at threshold
- recall at threshold
- F1 at threshold
- actioned count
- recall at Top-25
- recall at Top-50
- recall at Top-100
- recall at Top-5%
- recall at Top-10%

Current threshold grid:

- `0.50`
- `0.67`
- `0.80`
- `0.90`
- `0.95`

Current action threshold:

- `0.90`

### 3. Probability Quality

Report:

- calibration table
- Brier score
- calibration method

Current calibration:

- isotonic regression fitted on out-of-fold CatBoost scores

Scores are direct no-show probabilities. Higher means higher no-show risk.

## Split

Random split is not allowed for model quality claims.

Current split:

- train: 2015, 2016
- test: 2017

All headline metrics must be reported on the temporal test split.

## Model Under Evaluation

Only one active candidate is evaluated:

- `catboost_with_logistic_score`

Logistic Regression is an internal feeder score, not a displayed competitor.

## Stage Separation

Evaluate stages separately:

- `customer_pre_reservation`
- `reservation_post_booking`

Do not merge their metrics into one leaderboard. They answer different operational questions and have different feature availability.

## Required Outputs

Each training run should produce:

- `evaluation_summary.json`
- `model_comparison.csv`
- `<model>_threshold_metrics.csv`
- `<model>_top_k_metrics.csv`
- `<model>_calibration.csv`
- `feature_list.json`
- `feature_percentiles.csv`
- `feature_drift.csv`
- `risk_thresholds.json`
- `threshold_policy.json`
- `stacking_summary.json`

These are training artifacts for auditability. Product-facing summaries should stay concise and should not expose unnecessary model internals.

## Decision Rules

A stage should not be promoted if:

- PR-AUC is near random for the class prevalence
- calibrated scores are badly misaligned with observed rates
- the action threshold creates too many actions for operations
- top-k recall does not improve manual review prioritization
- drift indicates the test period is materially different from training without an explanation

Thresholds can be adjusted without retraining. Feature set, target, split, model parameters, and calibration changes require a new training run.

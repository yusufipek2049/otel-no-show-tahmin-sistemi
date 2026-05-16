# Model Evaluation Plan

## Objective

Evaluation needs to answer two practical questions:

- Can the model rank likely no-shows ahead of likely arrivals?
- At the chosen action threshold, is the workload worth the no-shows captured?

This is a rare-event problem, so accuracy is not a useful decision metric.

## Evaluation Layers

### 1. Ranking Quality

Primary metric:

- PR-AUC

Secondary metric:

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

Random split is not allowed for headline quality claims.

Current split:

- train: 2015, 2016
- test: 2017

All headline metrics must come from the temporal test split.

## Model Under Evaluation

Only one active candidate is evaluated:

- `catboost_with_logistic_score`

Logistic Regression is an internal feeder score, not a displayed competitor.

## Stage Separation

Evaluate stages separately:

- `customer_pre_reservation`
- `reservation_post_booking`

Do not merge their metrics into one leaderboard. They answer different operational questions and use different feature-availability policies.

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

These artifacts support auditability. Product-facing summaries should stay concise and avoid unnecessary model internals.

## Decision Rules

A stage should not be promoted if:

- PR-AUC is close to random for the class prevalence
- calibrated scores are badly misaligned with observed rates
- the action threshold creates more work than operations can handle
- Top-K recall does not improve manual review prioritization
- drift shows a materially different test period without a clear explanation

Thresholds can be adjusted without retraining. Changes to the feature set, target, split, model parameters, or calibration require a new training run.

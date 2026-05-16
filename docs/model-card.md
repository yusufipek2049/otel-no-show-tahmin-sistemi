# Model Card

## Model

Name:

- `catboost_with_logistic_score`

Stages:

- `customer_pre_reservation`
- `reservation_post_booking`

Model type:

- CatBoost binary classifier
- Logistic Regression feeder score
- isotonic probability calibration

## Intended Use

The model supports hotel operations teams by prioritizing customers or reservations that may require follow-up before arrival.

It should be used for decision support, not automatic punitive action.

## Not Intended For

- cancellation prediction
- guest creditworthiness scoring
- automated guest rejection
- marketing attribution
- generic revenue forecasting

## Score Meaning

The score is direct no-show probability.

Higher score means higher no-show risk.

Do not use `1.0 - score`.

## Thresholds

Current policy:

- action threshold: `0.90`
- high risk: `>= 0.80`
- medium risk: `>= 0.67`
- notable risk: `>= 0.50`
- low risk: `< 0.50`

## Inputs

Main input groups:

- booking and arrival context
- customer history
- payment failure signals
- communication signals
- campaign / channel signals
- guarantee and deposit signals

Operational signals are synthetic in the public H1/H2 proof-of-concept and must be replaced with real timestamped data for production use.

## Evaluation

Required metrics:

- PR-AUC
- ROC-AUC
- precision, recall, F1 at threshold
- actioned count
- recall at Top-K
- Brier score
- calibration table

Current observed artifact quality should be treated as proof-of-concept quality because the strongest operational signals are synthetic proxies.

## Risks

Main risks:

- target leakage from final-state fields
- overstated performance from random splits
- false positives creating unnecessary guest contact
- false negatives missing true no-shows
- synthetic signal overconfidence
- drift by season, channel, country, and campaign mix

## Required Monitoring

Monitor:

- score distribution
- calibration by score bin
- action volume above threshold
- precision and recall when labels become available
- feature drift
- missingness drift
- channel and segment performance

## Human Oversight

Operations users should review the context before acting. The score should prioritize workflow, not replace judgment.

# Model Candidate Policy

## Current Policy

The active candidate set intentionally contains one final model:

- `catboost_with_logistic_score`

This is not a broad benchmark project anymore. The product direction is a staged operational no-show system with a single stable model architecture.

## Why CatBoost

CatBoost remains the right default for this dataset shape because:

- the data is tabular
- categorical fields are important
- missing and sparse categories are expected
- feature interactions matter
- preprocessing cost should stay controlled

## Logistic Regression Role

Logistic Regression is retained as an internal feeder model.

It should:

- produce `logistic_regression_score`
- use out-of-fold training scores when feasible
- be saved as `logistic_regression_feeder.joblib`
- not appear as a separate product candidate

Reason:

- it gives CatBoost a stable linear baseline signal without creating a confusing two-model UI.

## Optional Future Benchmarks

LightGBM, XGBoost, Random Forest, neural tabular models, SVM, kNN, and Naive Bayes are not in the active candidate set.

They can be added only if there is a clear engineering reason, such as:

- CatBoost performance plateaus after real operational data is connected
- training latency becomes unacceptable
- deployment constraints favor a different library
- an explicit benchmark sprint is approved

Any optional benchmark must use the same temporal split, same feature policy, same target, and same threshold reporting.

## Selection Priority

When comparing future alternatives, use this order:

1. PR-AUC
2. Recall at Top-K
3. Precision at action threshold
4. Calibration / Brier score
5. ROC-AUC
6. production cost and maintainability

Accuracy must not be used as the model selection metric.

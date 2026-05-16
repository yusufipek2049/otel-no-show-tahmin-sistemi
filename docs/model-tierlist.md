# Model Candidate Policy

## Current Policy

The active candidate set intentionally contains one final model:

- `catboost_with_logistic_score`

This is no longer a broad benchmark project. The product direction is a staged operational no-show system with one stable model architecture.

## Why CatBoost

CatBoost is the right default for the current dataset shape because:

- the data is tabular
- categorical fields carry meaningful signal
- missing and sparse categories are expected
- feature interactions matter
- preprocessing cost should stay controlled

## Logistic Regression Role

Logistic Regression remains in the system as an internal feeder model.

It should:

- produce `logistic_regression_score`
- use out-of-fold training scores when feasible
- be saved as `logistic_regression_feeder.joblib`
- stay out of the product UI as a separate candidate

This gives CatBoost a stable linear baseline signal without turning the product into a confusing two-model comparison for users.

## Optional Future Benchmarks

LightGBM, XGBoost, Random Forest, neural tabular models, SVM, kNN, and Naive Bayes are not active candidates.

They can be added only when there is a clear engineering reason, such as:

- CatBoost performance plateaus after real operational data is connected
- training latency becomes unacceptable
- deployment constraints favor another library
- an explicit benchmark sprint is approved

Any optional benchmark must use the same temporal split, feature policy, target, and threshold reporting.

## Selection Priority

When comparing future alternatives, use this order:

1. PR-AUC
2. Recall at Top-K
3. Precision at action threshold
4. Calibration / Brier score
5. ROC-AUC
6. production cost and maintainability

Accuracy must not be used as the selection metric for this problem.

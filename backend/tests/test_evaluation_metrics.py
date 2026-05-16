from __future__ import annotations

import numpy as np
import pandas as pd

from app.training.evaluation import (
    build_calibration_table,
    build_threshold_metrics,
    build_top_k_metrics,
    compute_classification_metrics,
    score_to_risk_class,
)


def test_compute_classification_metrics_returns_threshold_confusion_counts() -> None:
    y_true = pd.Series([0, 1, 1, 0])
    y_score = np.array([0.10, 0.90, 0.40, 0.80])

    metrics = compute_classification_metrics(y_true, y_score, threshold=0.50)

    assert metrics["threshold"] == 0.50
    assert metrics["actioned_count"] == 2
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["roc_auc"] is not None
    assert metrics["pr_auc"] is not None
    assert metrics["brier_score"] >= 0


def test_build_threshold_metrics_returns_one_row_per_threshold() -> None:
    y_true = pd.Series([0, 1, 1, 0])
    y_score = np.array([0.10, 0.90, 0.40, 0.80])

    table = build_threshold_metrics(y_true, y_score, thresholds=(0.50, 0.90))

    assert table["threshold"].tolist() == [0.50, 0.90]
    assert table["actioned_count"].tolist() == [2, 1]
    assert {"precision", "recall", "f1"}.issubset(table.columns)


def test_build_top_k_metrics_counts_captured_positives() -> None:
    y_true = pd.Series([0, 1, 1, 0])
    y_score = np.array([0.10, 0.90, 0.40, 0.80])

    table = build_top_k_metrics(y_true, y_score, top_k_values=(1, 2), top_percent_values=(0.50,))

    top_one = table.loc[table["segment"] == "top_1"].iloc[0]
    top_two = table.loc[table["segment"] == "top_2"].iloc[0]
    top_half = table.loc[table["segment"] == "top_50pct"].iloc[0]

    assert top_one["selected_count"] == 1
    assert top_one["captured_no_show"] == 1
    assert top_one["total_no_show"] == 2
    assert top_two["selected_count"] == 2
    assert top_half["selected_count"] == 2


def test_build_calibration_table_returns_probability_bins() -> None:
    y_true = pd.Series([0, 1, 1, 0])
    y_score = np.array([0.10, 0.90, 0.40, 0.80])

    table = build_calibration_table(y_true, y_score, bin_count=2)

    assert len(table) == 2
    assert {"sample_count", "mean_predicted_probability", "observed_positive_rate"}.issubset(table.columns)
    assert int(table["sample_count"].sum()) == 4


def test_score_to_risk_class_uses_current_bands() -> None:
    assert score_to_risk_class(0.91) == "high"
    assert score_to_risk_class(0.70) == "medium"
    assert score_to_risk_class(0.55) == "notable"
    assert score_to_risk_class(0.20) == "low"


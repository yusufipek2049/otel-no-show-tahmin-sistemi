from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.training.constants import ACTION_THRESHOLD, CALIBRATION_BIN_COUNT, HIGH_RISK_THRESHOLD, TOP_K_VALUES, TOP_PERCENT_VALUES


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int, np.floating, np.integer)):
        if np.isnan(value):
            return None
        return float(value)
    return float(value)


def _safe_roc_auc(y_true: pd.Series, y_score: np.ndarray) -> float | None:
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def compute_classification_metrics(
    y_true: pd.Series,
    y_score: np.ndarray,
    *,
    threshold: float = ACTION_THRESHOLD,
) -> dict[str, Any]:
    predictions = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()

    return {
        "roc_auc": _safe_roc_auc(y_true, y_score),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_score)),
        "threshold": float(threshold),
        "actioned_count": int(predictions.sum()),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
    }


def build_threshold_metrics(y_true: pd.Series, y_score: np.ndarray, thresholds: tuple[float, ...]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for threshold in thresholds:
        predictions = (y_score >= threshold).astype(int)
        records.append(
            {
                "threshold": float(threshold),
                "precision": float(precision_score(y_true, predictions, zero_division=0)),
                "recall": float(recall_score(y_true, predictions, zero_division=0)),
                "f1": float(f1_score(y_true, predictions, zero_division=0)),
                "actioned_count": int(predictions.sum()),
            }
        )
    return pd.DataFrame(records)


def build_top_k_metrics(
    y_true: pd.Series,
    y_score: np.ndarray,
    *,
    top_k_values: tuple[int, ...] = TOP_K_VALUES,
    top_percent_values: tuple[float, ...] = TOP_PERCENT_VALUES,
) -> pd.DataFrame:
    scored = pd.DataFrame({"y_true": y_true.to_numpy(), "score": y_score}).sort_values("score", ascending=False).reset_index(drop=True)
    total_positives = int(scored["y_true"].sum())
    records: list[dict[str, Any]] = []

    for k in top_k_values:
        top_slice = scored.head(min(k, len(scored)))
        captured = int(top_slice["y_true"].sum())
        recall = captured / total_positives if total_positives else 0.0
        records.append(
            {
                "segment": f"top_{k}",
                "selected_count": int(len(top_slice)),
                "captured_no_show": captured,
                "total_no_show": total_positives,
                "recall": float(recall),
            }
        )

    for pct in top_percent_values:
        count = max(1, int(np.ceil(len(scored) * pct)))
        top_slice = scored.head(count)
        captured = int(top_slice["y_true"].sum())
        recall = captured / total_positives if total_positives else 0.0
        records.append(
            {
                "segment": f"top_{int(pct * 100)}pct",
                "selected_count": int(count),
                "captured_no_show": captured,
                "total_no_show": total_positives,
                "recall": float(recall),
            }
        )

    return pd.DataFrame(records)


def build_calibration_table(
    y_true: pd.Series,
    y_score: np.ndarray,
    *,
    bin_count: int = CALIBRATION_BIN_COUNT,
) -> pd.DataFrame:
    calibration_df = pd.DataFrame({"y_true": y_true.to_numpy(), "score": y_score})
    if calibration_df["score"].nunique() < 2:
        calibration_df["bin"] = 0
    else:
        calibration_df["bin"] = pd.qcut(
            calibration_df["score"].rank(method="first"),
            q=min(bin_count, len(calibration_df)),
            labels=False,
            duplicates="drop",
        )

    grouped = (
        calibration_df.groupby("bin", dropna=False)
        .agg(
            sample_count=("y_true", "size"),
            mean_predicted_probability=("score", "mean"),
            observed_positive_rate=("y_true", "mean"),
        )
        .reset_index()
    )
    return grouped


def score_to_risk_class(score: float) -> str:
    if score >= HIGH_RISK_THRESHOLD:
        return "high"
    if score >= ACTION_THRESHOLD:
        return "medium"
    return "low"

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.training.constants import DEFAULT_ARTIFACTS_ROOT


class ReportsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_bootstrap_benchmark_report(self) -> dict[str, object]:
        latest_summary_path = DEFAULT_ARTIFACTS_ROOT / "latest" / "reports" / "evaluation_summary.json"
        if latest_summary_path.exists():
            summary = json.loads(latest_summary_path.read_text(encoding="utf-8"))
            models = []
            for model_name, model_payload in summary.get("models", {}).items():
                metrics = [
                    {
                        "name": metric_name,
                        "value": metric_value,
                        "status": "available" if metric_value is not None else "pending",
                    }
                    for metric_name, metric_value in model_payload.get("metrics", {}).items()
                    if metric_name in {"pr_auc", "roc_auc", "precision", "recall", "f1", "brier_score"}
                ]
                models.append(
                    {
                        "model_name": model_name,
                        "status": "trained",
                        "notes": f"Version {model_payload['model_version']} evaluated from latest artifact.",
                        "metrics": metrics,
                    }
                )

            return {
                "split_strategy": "time-based split: train on 2015-2016, test on 2017",
                "primary_metrics": ["pr_auc", "roc_auc", "precision", "recall", "f1", "brier_score"],
                "models": models,
            }

        return {
            "split_strategy": "time-based split planned (train on earlier periods, validate on later periods)",
            "primary_metrics": ["pr_auc", "roc_auc", "precision", "recall", "f1", "calibration"],
            "models": [
                {
                    "model_name": "logistic_regression",
                    "status": "planned",
                    "notes": "Bootstrap scaffold only. Training pipeline lands in a later task.",
                    "metrics": [
                        {"name": "pr_auc", "value": None, "status": "pending"},
                        {"name": "roc_auc", "value": None, "status": "pending"},
                    ],
                },
                {
                    "model_name": "catboost",
                    "status": "planned",
                    "notes": "CatBoost remains the primary tabular candidate once ingestion and features are wired.",
                    "metrics": [
                        {"name": "pr_auc", "value": None, "status": "pending"},
                        {"name": "roc_auc", "value": None, "status": "pending"},
                    ],
                },
            ],
        }

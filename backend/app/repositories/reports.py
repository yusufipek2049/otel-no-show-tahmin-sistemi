from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import ReservationAction
from app.models.reservation import ReservationClean
from app.repositories.reservations import build_latest_prediction_subquery, prediction_store_has_rows
from app.training.constants import DEFAULT_ARTIFACTS_ROOT


class ReportsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.latest_predictions = build_latest_prediction_subquery()

    def has_prediction_data(self) -> bool:
        return prediction_store_has_rows(self.db)

    def _get_reporting_rows(self) -> list[dict[str, object]]:
        stmt = (
            select(
                ReservationClean.id.label("reservation_id"),
                ReservationClean.arrival_date.label("arrival_date"),
                ReservationClean.distribution_channel.label("distribution_channel"),
                ReservationClean.market_segment.label("market_segment"),
                ReservationClean.no_show_flag.label("no_show_flag"),
                ReservationClean.is_canceled.label("is_canceled"),
                ReservationClean.reservation_status.label("reservation_status"),
                self.latest_predictions.c.score.label("score"),
                self.latest_predictions.c.risk_class.label("risk_class"),
            )
            .select_from(ReservationClean)
            .outerjoin(
                self.latest_predictions,
                self.latest_predictions.c.reservation_clean_id == ReservationClean.id,
            )
        )
        return [dict(row) for row in self.db.execute(stmt).mappings().all()]

    def _get_actions(self) -> list[ReservationAction]:
        stmt = select(ReservationAction).order_by(ReservationAction.acted_at.desc(), ReservationAction.id.desc())
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def _is_canceled(row: dict[str, object]) -> bool:
        if row.get("is_canceled") is True:
            return True
        status = row.get("reservation_status")
        return isinstance(status, str) and status.lower() == "canceled"

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def _period_key(value) -> str:
        if value is None:
            return "unknown"
        return value.strftime("%Y-%m")

    @staticmethod
    def _dimension_key(value: object, fallback: str = "Unknown") -> str:
        if value is None:
            return fallback
        normalized = str(value).strip()
        return normalized or fallback

    def get_operations_summary(self) -> dict[str, object]:
        rows = self._get_reporting_rows()
        actions = self._get_actions()
        total_reservations = len(rows)
        scored_reservations = sum(1 for row in rows if row.get("score") is not None)
        no_show_count = sum(1 for row in rows if row.get("no_show_flag") is True)
        canceled_count = sum(1 for row in rows if self._is_canceled(row))
        high_risk_count = sum(1 for row in rows if row.get("risk_class") == "high")

        return {
            "total_reservations": total_reservations,
            "scored_reservations": scored_reservations,
            "no_show_count": no_show_count,
            "canceled_count": canceled_count,
            "no_show_rate": self._rate(no_show_count, total_reservations),
            "cancellation_rate": self._rate(canceled_count, total_reservations),
            "high_risk_reservations": high_risk_count,
            "action_pending_count": sum(1 for action in actions if action.action_status == "open"),
            "action_completed_count": sum(1 for action in actions if action.action_status == "completed"),
            "action_follow_up_count": sum(1 for action in actions if action.action_status == "follow_up"),
        }

    def get_no_show_trends(self) -> list[dict[str, object]]:
        buckets: dict[str, dict[str, object]] = {}
        for row in self._get_reporting_rows():
            period = self._period_key(row.get("arrival_date"))
            bucket = buckets.setdefault(
                period,
                {
                    "period": period,
                    "total_reservations": 0,
                    "no_show_count": 0,
                    "canceled_count": 0,
                },
            )
            bucket["total_reservations"] += 1
            if row.get("no_show_flag") is True:
                bucket["no_show_count"] += 1
            if self._is_canceled(row):
                bucket["canceled_count"] += 1

        results = []
        for period in sorted(buckets):
            bucket = buckets[period]
            total = int(bucket["total_reservations"])
            no_show_count = int(bucket["no_show_count"])
            canceled_count = int(bucket["canceled_count"])
            results.append(
                {
                    **bucket,
                    "no_show_rate": self._rate(no_show_count, total),
                    "cancellation_rate": self._rate(canceled_count, total),
                }
            )
        return results

    def get_dimension_breakdown(self, dimension: str) -> list[dict[str, object]]:
        if dimension not in {"distribution_channel", "market_segment"}:
            raise ValueError(f"Unsupported dimension: {dimension}")

        buckets: dict[str, dict[str, object]] = {}
        for row in self._get_reporting_rows():
            key = self._dimension_key(row.get(dimension))
            bucket = buckets.setdefault(
                key,
                {
                    "dimension_value": key,
                    "total_reservations": 0,
                    "scored_reservations": 0,
                    "high_risk_reservations": 0,
                    "no_show_count": 0,
                    "canceled_count": 0,
                    "scores": [],
                },
            )
            bucket["total_reservations"] += 1
            if row.get("score") is not None:
                bucket["scored_reservations"] += 1
                bucket["scores"].append(float(row["score"]))
            if row.get("risk_class") == "high":
                bucket["high_risk_reservations"] += 1
            if row.get("no_show_flag") is True:
                bucket["no_show_count"] += 1
            if self._is_canceled(row):
                bucket["canceled_count"] += 1

        results = []
        for key, bucket in buckets.items():
            total = int(bucket["total_reservations"])
            no_show_count = int(bucket["no_show_count"])
            canceled_count = int(bucket["canceled_count"])
            results.append(
                {
                    "dimension_value": key,
                    "total_reservations": total,
                    "scored_reservations": int(bucket["scored_reservations"]),
                    "high_risk_reservations": int(bucket["high_risk_reservations"]),
                    "no_show_count": no_show_count,
                    "canceled_count": canceled_count,
                    "no_show_rate": self._rate(no_show_count, total),
                    "cancellation_rate": self._rate(canceled_count, total),
                    "average_score": mean(bucket["scores"]) if bucket["scores"] else None,
                }
            )

        return sorted(results, key=lambda row: (-row["total_reservations"], row["dimension_value"]))

    def get_action_effectiveness(self) -> dict[str, object]:
        rows = self._get_reporting_rows()
        actions = self._get_actions()
        high_risk_reservation_ids = {
            int(row["reservation_id"])
            for row in rows
            if row.get("risk_class") == "high" and row.get("reservation_id") is not None
        }
        reservations_with_actions = {action.reservation_clean_id for action in actions}

        status_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        for action in actions:
            status_counts[action.action_status] = status_counts.get(action.action_status, 0) + 1
            type_counts[action.action_type] = type_counts.get(action.action_type, 0) + 1

        return {
            "total_actions": len(actions),
            "open_actions": status_counts.get("open", 0),
            "completed_actions": status_counts.get("completed", 0),
            "follow_up_actions": status_counts.get("follow_up", 0),
            "high_risk_with_action_count": len(high_risk_reservation_ids & reservations_with_actions),
            "high_risk_without_action_count": len(high_risk_reservation_ids - reservations_with_actions),
            "status_breakdown": [
                {"label": label, "count": count}
                for label, count in sorted(status_counts.items(), key=lambda item: (-item[1], item[0]))
            ],
            "type_breakdown": [
                {"label": label, "count": count}
                for label, count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
            ],
        }

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

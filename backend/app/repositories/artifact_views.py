from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.training.constants import DEFAULT_ARTIFACTS_ROOT


@dataclass
class ArtifactPaths:
    root: Path
    evaluation_summary: Path
    model_comparison: Path
    clean_dataset: Path


def _path_signature(path: Path) -> tuple[str, int]:
    return str(path), path.stat().st_mtime_ns


@lru_cache(maxsize=32)
def _read_json_cached(path_str: str, mtime_ns: int) -> dict[str, Any]:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


@lru_cache(maxsize=64)
def _read_csv_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(Path(path_str), low_memory=False)


def _safe_iso_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _safe_iso_datetime(value: Any) -> str | None:
    if value is None or value == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.isoformat()


def _safe_optional_str(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    return str(value)


class ArtifactViewRepository:
    def __init__(self, root: Path = DEFAULT_ARTIFACTS_ROOT / "latest") -> None:
        self.root = root

    def get_paths(self) -> ArtifactPaths:
        reports_dir = self.root / "reports"
        datasets_dir = self.root / "datasets"
        return ArtifactPaths(
            root=self.root,
            evaluation_summary=reports_dir / "evaluation_summary.json",
            model_comparison=reports_dir / "model_comparison.csv",
            clean_dataset=datasets_dir / "reservations_clean.csv",
        )

    def exists(self) -> bool:
        paths = self.get_paths()
        return paths.evaluation_summary.exists() and paths.clean_dataset.exists()

    def _load_json(self, path: Path) -> dict[str, Any]:
        return _read_json_cached(*_path_signature(path))

    def _load_csv(self, path: Path) -> pd.DataFrame:
        return _read_csv_cached(*_path_signature(path)).copy()

    def get_evaluation_summary(self) -> dict[str, Any]:
        return self._load_json(self.get_paths().evaluation_summary)

    def get_recommended_model_name(self) -> str:
        summary = self.get_evaluation_summary()
        return str(summary.get("recommended_model", "logistic_regression"))

    def get_recommended_model_version(self) -> str | None:
        summary = self.get_evaluation_summary()
        model_name = self.get_recommended_model_name()
        model_payload = summary.get("models", {}).get(model_name, {})
        return model_payload.get("model_version")

    def _get_prediction_path(self, model_name: str) -> Path:
        return self.root / "predictions" / f"{model_name}_predictions.csv"

    def get_prediction_frame(self, model_name: str | None = None) -> pd.DataFrame:
        selected_model = model_name or self.get_recommended_model_name()
        prediction_frame = self._load_csv(self._get_prediction_path(selected_model))
        prediction_frame["arrival_date"] = pd.to_datetime(prediction_frame["arrival_date"], errors="coerce")
        prediction_frame["scored_at"] = pd.to_datetime(prediction_frame["scored_at"], errors="coerce", utc=True)
        prediction_frame["score"] = pd.to_numeric(prediction_frame["score"], errors="coerce")
        prediction_frame["threshold_used"] = pd.to_numeric(prediction_frame["threshold_used"], errors="coerce")
        return prediction_frame

    def get_clean_dataset(self) -> pd.DataFrame:
        frame = self._load_csv(self.get_paths().clean_dataset)
        if "arrival_date" in frame.columns:
            frame["arrival_date"] = pd.to_datetime(frame["arrival_date"], errors="coerce")
        if "reservation_status_date" in frame.columns:
            frame["reservation_status_date"] = pd.to_datetime(frame["reservation_status_date"], errors="coerce")
        if "no_show_flag" in frame.columns:
            frame["no_show_flag"] = pd.to_numeric(frame["no_show_flag"], errors="coerce")
        if "excluded_from_training" in frame.columns:
            frame["excluded_from_training"] = frame["excluded_from_training"].fillna(False).astype(bool)
        return frame

    def get_reservation_view(self, model_name: str | None = None) -> pd.DataFrame:
        selected_model = model_name or self.get_recommended_model_name()
        selected_version = self.get_recommended_model_version()
        clean_frame = self.get_clean_dataset()
        prediction_frame = self.get_prediction_frame(selected_model)

        merged = clean_frame.merge(
            prediction_frame,
            on=["reservation_key", "source_file", "source_row_number"],
            how="right",
            suffixes=("", "_prediction"),
        )
        merged = merged.sort_values(["source_file", "source_row_number"]).reset_index(drop=True)
        merged["reservation_id"] = np.arange(1, len(merged) + 1)
        merged["score"] = pd.to_numeric(merged["score"], errors="coerce")
        merged["arrival_date"] = pd.to_datetime(merged["arrival_date"], errors="coerce")
        merged["risk_class"] = merged["risk_class"].fillna("unscored")
        merged["model_name"] = selected_model
        if selected_version:
            merged["model_version"] = merged["model_version"].fillna(selected_version)
        return merged

    def _filter_reservation_view(
        self,
        frame: pd.DataFrame,
        *,
        property_id: str | None = None,
        distribution_channel: str | None = None,
        risk_class: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> pd.DataFrame:
        filtered = frame.copy()
        if property_id:
            filtered = filtered.loc[filtered["property_id"] == property_id]
        if distribution_channel:
            filtered = filtered.loc[filtered["distribution_channel"] == distribution_channel]
        if risk_class:
            filtered = filtered.loc[filtered["risk_class"] == risk_class]
        if date_from:
            filtered = filtered.loc[filtered["arrival_date"].dt.date >= date_from]
        if date_to:
            filtered = filtered.loc[filtered["arrival_date"].dt.date <= date_to]
        return filtered

    def get_filter_options(self, frame: pd.DataFrame) -> dict[str, Any]:
        arrival_dates = frame["arrival_date"].dropna()
        return {
            "property_ids": sorted(frame["property_id"].dropna().astype(str).unique().tolist()),
            "distribution_channels": sorted(
                frame["distribution_channel"].dropna().astype(str).unique().tolist()
            ),
            "risk_classes": ["high", "medium", "low"],
            "min_arrival_date": arrival_dates.min().date() if not arrival_dates.empty else None,
            "max_arrival_date": arrival_dates.max().date() if not arrival_dates.empty else None,
            "model_name": self.get_recommended_model_name(),
            "model_version": self.get_recommended_model_version(),
        }

    def list_reservations(
        self,
        *,
        property_id: str | None = None,
        distribution_channel: str | None = None,
        risk_class: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
    ) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
        frame = self.get_reservation_view()
        filter_options = self.get_filter_options(frame)
        filtered = self._filter_reservation_view(
            frame,
            property_id=property_id,
            distribution_channel=distribution_channel,
            risk_class=risk_class,
            date_from=date_from,
            date_to=date_to,
        )
        filtered = filtered.sort_values(["score", "arrival_date", "reservation_id"], ascending=[False, False, True])
        page = filtered.head(limit)

        items = [
            {
                "reservation_id": int(record["reservation_id"]),
                "property_id": record["property_id"],
                "source_file": record["source_file"],
                "arrival_date": _safe_iso_date(record["arrival_date"]),
                "distribution_channel": record.get("distribution_channel"),
                "customer_type": _safe_optional_str(record.get("customer_type")),
                "no_show_flag": None
                if pd.isna(record.get("no_show_flag"))
                else bool(int(record.get("no_show_flag"))),
                "score": float(record["score"]) if pd.notna(record["score"]) else None,
                "risk_class": _safe_optional_str(record.get("risk_class")),
                "model_name": _safe_optional_str(record.get("model_name")),
                "model_version": _safe_optional_str(record.get("model_version")),
                "scored_at": _safe_iso_datetime(record.get("scored_at")),
            }
            for record in page.to_dict(orient="records")
        ]

        return int(len(filtered)), items, filter_options

    def get_reservation_detail(self, reservation_id: int) -> dict[str, Any] | None:
        frame = self.get_reservation_view()
        match = frame.loc[frame["reservation_id"] == reservation_id]
        if match.empty:
            return None

        record = match.iloc[0].to_dict()
        latest_prediction = {
            "reservation_id": int(record["reservation_id"]),
            "property_id": record["property_id"],
            "source_file": record["source_file"],
            "arrival_date": _safe_iso_date(record["arrival_date"]),
            "distribution_channel": _safe_optional_str(record.get("distribution_channel")),
            "customer_type": _safe_optional_str(record.get("customer_type")),
            "no_show_flag": None if pd.isna(record.get("no_show_flag")) else bool(int(record.get("no_show_flag"))),
            "score": float(record["score"]) if pd.notna(record["score"]) else None,
            "risk_class": _safe_optional_str(record.get("risk_class")),
            "model_name": _safe_optional_str(record.get("model_name")),
            "model_version": _safe_optional_str(record.get("model_version")),
            "scored_at": _safe_iso_datetime(record.get("scored_at")),
        }

        return {
            "reservation_id": int(record["reservation_id"]),
            "property_id": record["property_id"],
            "source_file": record["source_file"],
            "arrival_date": _safe_iso_date(record["arrival_date"]),
            "lead_time_days": int(record["lead_time_days"]) if pd.notna(record.get("lead_time_days")) else None,
            "distribution_channel": _safe_optional_str(record.get("distribution_channel")),
            "market_segment": _safe_optional_str(record.get("market_segment")),
            "customer_type": _safe_optional_str(record.get("customer_type")),
            "reserved_room_type": _safe_optional_str(record.get("reserved_room_type")),
            "deposit_type": _safe_optional_str(record.get("deposit_type")),
            "no_show_flag": None if pd.isna(record.get("no_show_flag")) else bool(int(record.get("no_show_flag"))),
            "excluded_from_training": bool(record.get("excluded_from_training", False)),
            "exclusion_reason": _safe_optional_str(record.get("exclusion_reason")),
            "latest_prediction": latest_prediction,
            "context": {
                "meal_plan": _safe_optional_str(record.get("meal_plan")),
                "is_repeated_guest": None
                if pd.isna(record.get("is_repeated_guest"))
                else bool(int(record.get("is_repeated_guest"))),
                "total_special_requests": int(record["total_special_requests"])
                if pd.notna(record.get("total_special_requests"))
                else None,
                "required_car_parking_spaces": int(record["required_car_parking_spaces"])
                if pd.notna(record.get("required_car_parking_spaces"))
                else None,
            },
        }

    def get_dashboard_summary(self, limit: int = 12) -> dict[str, Any]:
        frame = self.get_reservation_view()
        risky = frame.loc[frame["risk_class"].isin(["high", "medium"])].copy()
        risky = risky.sort_values(["score", "arrival_date", "reservation_id"], ascending=[False, False, True])
        latest_scored_at = frame["scored_at"].dropna()

        items = [
            {
                "reservation_id": int(record["reservation_id"]),
                "property_id": record["property_id"],
                "arrival_date": _safe_iso_date(record["arrival_date"]),
                "distribution_channel": record.get("distribution_channel"),
                "risk_class": record.get("risk_class"),
                "score": float(record["score"]) if pd.notna(record["score"]) else None,
                "model_version": record.get("model_version"),
            }
            for record in risky.head(limit).to_dict(orient="records")
        ]

        return {
            "kpis": {
                "total_reservations": int(len(frame)),
                "high_risk_reservations": int((frame["risk_class"] == "high").sum()),
                "medium_risk_reservations": int((frame["risk_class"] == "medium").sum()),
                "latest_scored_at": _safe_iso_datetime(latest_scored_at.max()) if not latest_scored_at.empty else None,
                "active_model_name": self.get_recommended_model_name(),
                "active_model_version": self.get_recommended_model_version(),
            },
            "items": items,
        }

    def get_benchmark_report(self) -> dict[str, Any]:
        summary = self.get_evaluation_summary()
        comparison = self._load_csv(self.get_paths().model_comparison)
        recommended_model = summary.get("recommended_model")
        selected_threshold = summary.get("selected_threshold")

        models = []
        threshold_tables: dict[str, list[dict[str, Any]]] = {}
        top_k_tables: dict[str, list[dict[str, Any]]] = {}

        for model_name, payload in summary.get("models", {}).items():
            metrics = [
                {
                    "name": metric_name,
                    "value": metric_value,
                    "status": "available" if metric_value is not None else "pending",
                }
                for metric_name, metric_value in payload.get("metrics", {}).items()
                if metric_name in {"pr_auc", "roc_auc", "precision", "recall", "f1", "brier_score"}
            ]
            models.append(
                {
                    "model_name": model_name,
                    "status": "trained",
                    "notes": f"Version {payload['model_version']} evaluated from latest artifact.",
                    "metrics": metrics,
                }
            )

            threshold_frame = self._load_csv(self.root / "reports" / f"{model_name}_threshold_metrics.csv")
            top_k_frame = self._load_csv(self.root / "reports" / f"{model_name}_top_k_metrics.csv")
            threshold_tables[model_name] = threshold_frame.to_dict(orient="records")
            top_k_tables[model_name] = top_k_frame.to_dict(orient="records")

        comparison_rows = comparison.to_dict(orient="records")
        highlight_lookup = {row["model_name"]: row for row in comparison_rows}
        recommendation_reason = None
        if recommended_model and recommended_model in highlight_lookup:
            row = highlight_lookup[recommended_model]
            recommendation_reason = (
                f"Recommended by latest artifact because it leads on PR-AUC "
                f"({row['pr_auc']:.3f}) under the current selection policy."
            )

        return {
            "split_strategy": "time-based split: train on 2015-2016, test on 2017",
            "primary_metrics": ["pr_auc", "roc_auc", "precision", "recall", "f1", "brier_score"],
            "recommended_model": recommended_model,
            "selected_threshold": selected_threshold,
            "recommendation_reason": recommendation_reason,
            "models": models,
            "comparison": comparison_rows,
            "threshold_tables": threshold_tables,
            "top_k_tables": top_k_tables,
        }

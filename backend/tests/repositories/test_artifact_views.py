from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.repositories.artifact_views import ArtifactViewRepository


def _write_artifact_fixture(root: Path) -> None:
    (root / "reports").mkdir(parents=True, exist_ok=True)
    (root / "datasets").mkdir(parents=True, exist_ok=True)
    (root / "predictions").mkdir(parents=True, exist_ok=True)

    clean_df = pd.DataFrame(
        [
            {
                "reservation_key": "H1.csv:1",
                "source_file": "H1.csv",
                "source_row_number": 1,
                "property_id": "RESORT_H1",
                "arrival_date": "2017-01-01",
                "lead_time_days": 25,
                "distribution_channel": "Direct",
                "market_segment": "Direct",
                "customer_type": "Transient",
                "reserved_room_type": "A",
                "deposit_type": "No Deposit",
                "no_show_flag": 1,
                "excluded_from_training": False,
                "exclusion_reason": None,
                "meal_plan": "BB",
                "is_repeated_guest": 0,
                "total_special_requests": 1,
                "required_car_parking_spaces": 0,
            },
            {
                "reservation_key": "H2.csv:2",
                "source_file": "H2.csv",
                "source_row_number": 2,
                "property_id": "CITY_H2",
                "arrival_date": "2017-01-05",
                "lead_time_days": 4,
                "distribution_channel": "TA/TO",
                "market_segment": "Online TA",
                "customer_type": "Contract",
                "reserved_room_type": "C",
                "deposit_type": "No Deposit",
                "no_show_flag": 0,
                "excluded_from_training": False,
                "exclusion_reason": None,
                "meal_plan": "HB",
                "is_repeated_guest": 1,
                "total_special_requests": 0,
                "required_car_parking_spaces": 1,
            },
        ]
    )
    clean_df.to_csv(root / "datasets" / "reservations_clean.csv", index=False)

    prediction_df = pd.DataFrame(
        [
            {
                "reservation_key": "H1.csv:1",
                "source_file": "H1.csv",
                "source_row_number": 1,
                "arrival_date": "2017-01-01",
                "actual_no_show_flag": 1,
                "feature_set_version": "booking_time_v1",
                "split_name": "test",
                "model_name": "logistic_regression",
                "model_version": "logreg_fixture",
                "score": 0.81,
                "risk_class": "high",
                "threshold_used": 0.35,
                "scoring_run_id": "fixture-run",
                "scored_at": "2026-04-12T00:00:00+00:00",
            },
            {
                "reservation_key": "H2.csv:2",
                "source_file": "H2.csv",
                "source_row_number": 2,
                "arrival_date": "2017-01-05",
                "actual_no_show_flag": 0,
                "feature_set_version": "booking_time_v1",
                "split_name": "test",
                "model_name": "logistic_regression",
                "model_version": "logreg_fixture",
                "score": 0.22,
                "risk_class": "low",
                "threshold_used": 0.35,
                "scoring_run_id": "fixture-run",
                "scored_at": "2026-04-12T00:00:00+00:00",
            },
        ]
    )
    prediction_df.to_csv(root / "predictions" / "logistic_regression_predictions.csv", index=False)

    comparison_df = pd.DataFrame(
        [
            {
                "model_name": "logistic_regression",
                "model_version": "logreg_fixture",
                "roc_auc": 0.81,
                "pr_auc": 0.09,
                "precision": 0.03,
                "recall": 0.80,
                "f1": 0.06,
                "brier_score": 0.19,
                "threshold": 0.35,
            }
        ]
    )
    comparison_df.to_csv(root / "reports" / "model_comparison.csv", index=False)

    pd.DataFrame(
        [
            {"threshold": 0.35, "precision": 0.03, "recall": 0.80, "f1": 0.06, "actioned_count": 1},
            {"threshold": 0.50, "precision": 0.05, "recall": 0.60, "f1": 0.09, "actioned_count": 1},
        ]
    ).to_csv(root / "reports" / "logistic_regression_threshold_metrics.csv", index=False)

    pd.DataFrame(
        [
            {"segment": "top_25", "selected_count": 2, "captured_no_show": 1, "total_no_show": 1, "recall": 1.0},
            {"segment": "top_50", "selected_count": 2, "captured_no_show": 1, "total_no_show": 1, "recall": 1.0},
        ]
    ).to_csv(root / "reports" / "logistic_regression_top_k_metrics.csv", index=False)

    summary = {
        "recommended_model": "logistic_regression",
        "selected_threshold": 0.35,
        "models": {
            "logistic_regression": {
                "model_version": "logreg_fixture",
                "metrics": {
                    "roc_auc": 0.81,
                    "pr_auc": 0.09,
                    "precision": 0.03,
                    "recall": 0.80,
                    "f1": 0.06,
                    "brier_score": 0.19,
                },
            }
        },
    }
    (root / "reports" / "evaluation_summary.json").write_text(json.dumps(summary), encoding="utf-8")


def test_artifact_repository_lists_and_filters_reservations(tmp_path: Path) -> None:
    fixture_root = tmp_path / "latest"
    _write_artifact_fixture(fixture_root)
    repository = ArtifactViewRepository(fixture_root)

    total, items, filters = repository.list_reservations(property_id="RESORT_H1")

    assert total == 1
    assert items[0]["property_id"] == "RESORT_H1"
    assert filters["model_name"] == "logistic_regression"
    assert "TA/TO" in filters["distribution_channels"]


def test_artifact_repository_returns_detail_view(tmp_path: Path) -> None:
    fixture_root = tmp_path / "latest"
    _write_artifact_fixture(fixture_root)
    repository = ArtifactViewRepository(fixture_root)

    detail = repository.get_reservation_detail(1)

    assert detail is not None
    assert detail["latest_prediction"]["score"] == 0.81
    assert detail["context"]["meal_plan"] == "BB"


def test_artifact_repository_builds_report_payload(tmp_path: Path) -> None:
    fixture_root = tmp_path / "latest"
    _write_artifact_fixture(fixture_root)
    repository = ArtifactViewRepository(fixture_root)

    report = repository.get_benchmark_report()

    assert report["recommended_model"] == "logistic_regression"
    assert report["comparison"][0]["pr_auc"] == 0.09
    assert report["threshold_tables"]["logistic_regression"][0]["threshold"] == 0.35
    assert report["top_k_tables"]["logistic_regression"][0]["segment"] == "top_25"


def test_artifact_repository_builds_management_payloads(tmp_path: Path) -> None:
    fixture_root = tmp_path / "latest"
    _write_artifact_fixture(fixture_root)
    repository = ArtifactViewRepository(fixture_root)

    summary = repository.get_operations_summary()
    trends = repository.get_no_show_trends()
    channel_breakdown = repository.get_dimension_breakdown("distribution_channel")
    action_effectiveness = repository.get_action_effectiveness()

    assert summary["total_reservations"] == 2
    assert summary["no_show_count"] == 1
    assert trends[0]["period"] == "2017-01"
    assert channel_breakdown[0]["dimension_value"] in {"Direct", "TA/TO"}
    assert action_effectiveness["total_actions"] == 0

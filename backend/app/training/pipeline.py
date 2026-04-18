from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.training.constants import ACTION_THRESHOLD, DEFAULT_ARTIFACTS_ROOT, THRESHOLDS
from app.training.evaluation import (
    build_calibration_table,
    build_threshold_metrics,
    build_top_k_metrics,
    compute_classification_metrics,
    score_to_risk_class,
)
from app.training.persistence import dataframe_to_json_records, refresh_latest_artifacts, write_dataframe, write_json
from app.training.schemas import ModelRunArtifacts, TemporalSplitBundle, TrainingRunArtifacts
from app.training.stages import ModelStageConfig


def _prepare_model_inputs(frame: pd.DataFrame, stage_config: ModelStageConfig) -> tuple[pd.DataFrame, pd.Series]:
    feature_policy = stage_config.feature_policy
    features = frame[list(feature_policy.model_feature_columns)].copy()

    for column in feature_policy.numeric_feature_columns:
        features[column] = pd.to_numeric(features[column], errors="coerce").astype(float)

    for column in feature_policy.categorical_feature_columns:
        features[column] = features[column].astype("object")
        features[column] = features[column].where(features[column].notna(), np.nan)

    return features, frame["no_show_flag"].astype(int).copy()


def _build_logistic_pipeline(stage_config: ModelStageConfig) -> Pipeline:
    feature_policy = stage_config.feature_policy
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, list(feature_policy.numeric_feature_columns)),
            ("categorical", categorical_pipeline, list(feature_policy.categorical_feature_columns)),
        ]
    )
    model = LogisticRegression(
        solver="saga",
        max_iter=4000,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def _train_logistic_regression(
    split_bundle: TemporalSplitBundle,
    stage_config: ModelStageConfig,
) -> tuple[Pipeline, np.ndarray]:
    X_train, y_train = _prepare_model_inputs(split_bundle.train_df, stage_config)
    X_test, _ = _prepare_model_inputs(split_bundle.test_df, stage_config)

    pipeline = _build_logistic_pipeline(stage_config)
    pipeline.fit(X_train, y_train)
    probabilities = pipeline.predict_proba(X_test)[:, 1]
    return pipeline, probabilities


def _train_catboost(
    split_bundle: TemporalSplitBundle,
    stage_config: ModelStageConfig,
) -> tuple[CatBoostClassifier, np.ndarray]:
    X_train, y_train = _prepare_model_inputs(split_bundle.train_df, stage_config)
    X_test, _ = _prepare_model_inputs(split_bundle.test_df, stage_config)

    X_train = X_train.copy()
    X_test = X_test.copy()
    for column in stage_config.feature_policy.categorical_feature_columns:
        X_train[column] = X_train[column].fillna("UNKNOWN").astype(str)
        X_test[column] = X_test[column].fillna("UNKNOWN").astype(str)

    cat_features = [X_train.columns.get_loc(column) for column in stage_config.feature_policy.categorical_feature_columns]
    model = CatBoostClassifier(
        loss_function="Logloss",
        eval_metric="PRAUC",
        auto_class_weights="Balanced",
        iterations=250,
        learning_rate=0.05,
        depth=6,
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(X_train, y_train, cat_features=cat_features)
    probabilities = model.predict_proba(X_test)[:, 1]
    return model, probabilities


def _build_prediction_frame(
    split_bundle: TemporalSplitBundle,
    probabilities: np.ndarray,
    *,
    model_name: str,
    model_version: str,
    scoring_run_id: str,
    stage_config: ModelStageConfig,
    threshold: float = ACTION_THRESHOLD,
) -> pd.DataFrame:
    columns = [
        "reservation_key",
        "source_file",
        "source_row_number",
        "arrival_date",
        "no_show_flag",
        "feature_set_version",
        "model_stage",
    ]
    for optional_column in ("snapshot_stage", "snapshot_at", "days_since_booking", "days_to_arrival"):
        if optional_column in split_bundle.test_df.columns:
            columns.append(optional_column)

    prediction_frame = split_bundle.test_df[columns].copy()
    prediction_frame.rename(columns={"no_show_flag": "actual_no_show_flag"}, inplace=True)
    prediction_frame["split_name"] = "test"
    prediction_frame["model_name"] = model_name
    prediction_frame["model_version"] = model_version
    prediction_frame["score"] = probabilities
    prediction_frame["risk_class"] = prediction_frame["score"].map(score_to_risk_class)
    prediction_frame["threshold_used"] = threshold
    prediction_frame["scoring_run_id"] = scoring_run_id
    prediction_frame["scored_at"] = datetime.now(timezone.utc).isoformat()
    prediction_frame["model_stage"] = stage_config.stage.value
    if "snapshot_stage" not in prediction_frame.columns:
        prediction_frame["snapshot_stage"] = stage_config.stage.value
    return prediction_frame


def _evaluate_model(
    *,
    split_bundle: TemporalSplitBundle,
    probabilities: np.ndarray,
    model_name: str,
    model_version: str,
    model_path: Path,
    scoring_run_id: str,
    stage_config: ModelStageConfig,
) -> ModelRunArtifacts:
    y_test = split_bundle.test_df["no_show_flag"].astype(int)
    metrics = compute_classification_metrics(y_test, probabilities, threshold=ACTION_THRESHOLD)
    threshold_metrics = build_threshold_metrics(y_test, probabilities, thresholds=THRESHOLDS)
    top_k_metrics = build_top_k_metrics(y_test, probabilities)
    calibration_table = build_calibration_table(y_test, probabilities)
    predictions = _build_prediction_frame(
        split_bundle,
        probabilities,
        model_name=model_name,
        model_version=model_version,
        scoring_run_id=scoring_run_id,
        stage_config=stage_config,
        threshold=ACTION_THRESHOLD,
    )

    return ModelRunArtifacts(
        model_name=model_name,
        model_version=model_version,
        metrics=metrics,
        threshold_metrics=threshold_metrics,
        top_k_metrics=top_k_metrics,
        calibration_table=calibration_table,
        predictions=predictions,
        model_path=model_path,
    )


def run_training_pipeline(
    *,
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    split_bundle: TemporalSplitBundle,
    import_summary: dict[str, Any],
    stage_config: ModelStageConfig,
    output_root: Path = DEFAULT_ARTIFACTS_ROOT,
) -> tuple[TrainingRunArtifacts, dict[str, ModelRunArtifacts]]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    scoring_run_id = f"{stage_config.stage.value}-{timestamp}"
    run_dir = output_root / timestamp
    latest_dir = output_root / "latest"
    models_dir = run_dir / "models"
    reports_dir = run_dir / "reports"
    predictions_dir = run_dir / "predictions"
    datasets_dir = run_dir / "datasets"

    for directory in (models_dir, reports_dir, predictions_dir, datasets_dir):
        directory.mkdir(parents=True, exist_ok=True)

    logistic_model, logistic_probabilities = _train_logistic_regression(split_bundle, stage_config)
    logistic_model_path = models_dir / "logistic_regression.joblib"
    joblib.dump(logistic_model, logistic_model_path)

    catboost_model, catboost_probabilities = _train_catboost(split_bundle, stage_config)
    catboost_model_path = models_dir / "catboost_model.cbm"
    catboost_model.save_model(str(catboost_model_path))

    model_artifacts = {
        "logistic_regression": _evaluate_model(
            split_bundle=split_bundle,
            probabilities=logistic_probabilities,
            model_name="logistic_regression",
            model_version=f"logreg_{timestamp}",
            model_path=logistic_model_path,
            scoring_run_id=scoring_run_id,
            stage_config=stage_config,
        ),
        "catboost": _evaluate_model(
            split_bundle=split_bundle,
            probabilities=catboost_probabilities,
            model_name="catboost",
            model_version=f"catboost_{timestamp}",
            model_path=catboost_model_path,
            scoring_run_id=scoring_run_id,
            stage_config=stage_config,
        ),
    }

    comparison_records = []
    prediction_paths: dict[str, Path] = {}
    model_paths = {name: artifact.model_path for name, artifact in model_artifacts.items()}
    for model_name, artifact in model_artifacts.items():
        comparison_records.append(
            {
                "model_stage": stage_config.stage.value,
                "model_name": model_name,
                "model_version": artifact.model_version,
                "roc_auc": artifact.metrics["roc_auc"],
                "pr_auc": artifact.metrics["pr_auc"],
                "precision": artifact.metrics["precision"],
                "recall": artifact.metrics["recall"],
                "f1": artifact.metrics["f1"],
                "brier_score": artifact.metrics["brier_score"],
                "threshold": artifact.metrics["threshold"],
            }
        )

        write_dataframe(artifact.threshold_metrics, reports_dir / f"{model_name}_threshold_metrics.csv")
        write_dataframe(artifact.top_k_metrics, reports_dir / f"{model_name}_top_k_metrics.csv")
        write_dataframe(artifact.calibration_table, reports_dir / f"{model_name}_calibration.csv")
        prediction_path = predictions_dir / f"{model_name}_predictions.csv"
        write_dataframe(artifact.predictions, prediction_path)
        prediction_paths[model_name] = prediction_path

    comparison_df = pd.DataFrame(comparison_records).sort_values(["pr_auc", "roc_auc"], ascending=False)
    recommended_model = comparison_df.iloc[0]["model_name"]

    feature_list_path = reports_dir / "feature_list.json"
    import_summary_path = reports_dir / "import_summary.json"
    split_summary_path = reports_dir / "split_summary.json"
    comparison_table_path = reports_dir / "model_comparison.csv"
    evaluation_summary_path = reports_dir / "evaluation_summary.json"
    clean_dataset_path = datasets_dir / "reservations_clean.csv"
    feature_dataset_path = datasets_dir / "reservation_features.csv"

    write_json(feature_list_path, stage_config.feature_policy.to_machine_readable_dict() | {"model_stage": stage_config.stage.value})
    write_json(import_summary_path, import_summary)
    write_json(
        split_summary_path,
        {
            "model_stage": stage_config.stage.value,
            "split_year_column": split_bundle.split_year_column,
            "train_years": sorted(split_bundle.train_df[split_bundle.split_year_column].unique().tolist()),
            "test_years": sorted(split_bundle.test_df[split_bundle.split_year_column].unique().tolist()),
            "train_row_count": int(len(split_bundle.train_df)),
            "test_row_count": int(len(split_bundle.test_df)),
            "train_class_distribution": split_bundle.train_df["no_show_flag"].value_counts().sort_index().to_dict(),
            "test_class_distribution": split_bundle.test_df["no_show_flag"].value_counts().sort_index().to_dict(),
        },
    )
    write_dataframe(comparison_df, comparison_table_path)
    write_dataframe(clean_df, clean_dataset_path)
    write_dataframe(feature_df, feature_dataset_path)

    write_json(
        evaluation_summary_path,
        {
            "scoring_run_id": scoring_run_id,
            "model_stage": stage_config.stage.value,
            "feature_set_version": stage_config.feature_set_version,
            "recommended_model": recommended_model,
            "selected_threshold": ACTION_THRESHOLD,
            "comparison": dataframe_to_json_records(comparison_df),
            "models": {
                model_name: {
                    "model_version": artifact.model_version,
                    "metrics": artifact.metrics,
                    "model_path": str(artifact.model_path),
                    "prediction_path": str(prediction_paths[model_name]),
                }
                for model_name, artifact in model_artifacts.items()
            },
        },
    )

    refresh_latest_artifacts(run_dir, latest_dir)

    return (
        TrainingRunArtifacts(
            model_stage=stage_config.stage.value,
            run_dir=run_dir,
            latest_dir=latest_dir,
            feature_list_path=feature_list_path,
            import_summary_path=import_summary_path,
            clean_dataset_path=clean_dataset_path,
            feature_dataset_path=feature_dataset_path,
            split_summary_path=split_summary_path,
            comparison_table_path=comparison_table_path,
            evaluation_summary_path=evaluation_summary_path,
            prediction_paths=prediction_paths,
            model_paths=model_paths,
        ),
        model_artifacts,
    )

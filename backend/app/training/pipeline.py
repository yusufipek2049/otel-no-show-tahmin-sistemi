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
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.core.logging import get_logger, log_event
from app.training.constants import (
    ACTION_THRESHOLD,
    CALIBRATION_METHOD,
    DEFAULT_ARTIFACTS_ROOT,
    OPERATIONAL_ACTION_CAPACITY,
    RISK_CLASS_BANDS,
    STACKING_CV_FOLDS,
    THRESHOLD_SELECTION_POLICY,
    THRESHOLDS,
)
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

logger = get_logger(__name__)


FEATURE_PERCENTILE_POINTS = (0.01, 0.05, 0.10, 0.20, 0.25, 0.33, 0.50, 0.66, 0.75, 0.80, 0.90, 0.95, 0.99)
DRIFT_QUANTILE_BINS = 10


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
        max_iter=8000,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def _resolve_cv_fold_count(y: pd.Series, requested_folds: int = STACKING_CV_FOLDS) -> int:
    class_counts = y.value_counts()
    if class_counts.size < 2:
        return 0
    minority_count = int(class_counts.min())
    return min(requested_folds, minority_count) if minority_count >= 2 else 0


def _train_logistic_regression(
    split_bundle: TemporalSplitBundle,
    stage_config: ModelStageConfig,
) -> tuple[Pipeline, np.ndarray, np.ndarray, dict[str, Any]]:
    X_train, y_train = _prepare_model_inputs(split_bundle.train_df, stage_config)
    X_test, _ = _prepare_model_inputs(split_bundle.test_df, stage_config)

    fold_count = _resolve_cv_fold_count(y_train)
    logger.info(log_event("feeder_training_started", cv_folds=fold_count, train_rows=len(X_train)))
    train_probabilities = np.full(len(X_train), np.nan)
    if fold_count:
        cv = StratifiedKFold(n_splits=fold_count, shuffle=True, random_state=42)
        for train_index, validation_index in cv.split(X_train, y_train):
            fold_pipeline = _build_logistic_pipeline(stage_config)
            fold_pipeline.fit(X_train.iloc[train_index], y_train.iloc[train_index])
            train_probabilities[validation_index] = fold_pipeline.predict_proba(X_train.iloc[validation_index])[:, 1]

    pipeline = _build_logistic_pipeline(stage_config)
    pipeline.fit(X_train, y_train)
    if np.isnan(train_probabilities).any():
        train_probabilities = pipeline.predict_proba(X_train)[:, 1]
    test_probabilities = pipeline.predict_proba(X_test)[:, 1]
    diagnostics = {
        "feeder_model": "logistic_regression",
        "stacking_score_source": "out_of_fold" if fold_count else "in_sample_fallback",
        "cv_folds": fold_count,
    }
    logger.info(
        log_event(
            "feeder_training_completed",
            model_name="logistic_regression",
            score_source=diagnostics["stacking_score_source"],
        )
    )
    return pipeline, train_probabilities, test_probabilities, diagnostics


def _train_catboost(
    split_bundle: TemporalSplitBundle,
    stage_config: ModelStageConfig,
) -> tuple[CatBoostClassifier, np.ndarray, np.ndarray]:
    X_train, y_train = _prepare_model_inputs(split_bundle.train_df, stage_config)
    X_test, _ = _prepare_model_inputs(split_bundle.test_df, stage_config)
    logistic_train_probabilities = split_bundle.train_df.get("logistic_regression_score")
    logistic_test_probabilities = split_bundle.test_df.get("logistic_regression_score")
    if logistic_train_probabilities is not None and logistic_test_probabilities is not None:
        X_train = X_train.assign(logistic_regression_score=logistic_train_probabilities.to_numpy())
        X_test = X_test.assign(logistic_regression_score=logistic_test_probabilities.to_numpy())

    X_train = X_train.copy()
    X_test = X_test.copy()
    for column in stage_config.feature_policy.categorical_feature_columns:
        X_train[column] = X_train[column].fillna("UNKNOWN").astype(str)
        X_test[column] = X_test[column].fillna("UNKNOWN").astype(str)

    cat_features = [
        X_train.columns.get_loc(column)
        for column in stage_config.feature_policy.categorical_feature_columns
        if column in X_train.columns
    ]
    model = CatBoostClassifier(
        loss_function="Logloss",
        eval_metric="PRAUC",
        auto_class_weights="Balanced",
        iterations=400,
        learning_rate=0.05,
        depth=6,
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
    )
    logger.info(
        log_event(
            "catboost_training_started",
            model_name="catboost_with_logistic_score",
            train_rows=len(X_train),
            test_rows=len(X_test),
        )
    )
    model.fit(X_train, y_train, cat_features=cat_features)
    train_probabilities = model.predict_proba(X_train)[:, 1]
    test_probabilities = model.predict_proba(X_test)[:, 1]
    logger.info(log_event("catboost_training_completed", model_name="catboost_with_logistic_score"))
    return model, train_probabilities, test_probabilities


def _train_catboost_oof_predictions(split_bundle: TemporalSplitBundle, stage_config: ModelStageConfig) -> tuple[np.ndarray, dict[str, Any]]:
    X_train, y_train = _prepare_model_inputs(split_bundle.train_df, stage_config)
    logistic_train_probabilities = split_bundle.train_df.get("logistic_regression_score")
    if logistic_train_probabilities is not None:
        X_train = X_train.assign(logistic_regression_score=logistic_train_probabilities.to_numpy())

    X_train = X_train.copy()
    for column in stage_config.feature_policy.categorical_feature_columns:
        X_train[column] = X_train[column].fillna("UNKNOWN").astype(str)

    cat_features = [
        X_train.columns.get_loc(column)
        for column in stage_config.feature_policy.categorical_feature_columns
        if column in X_train.columns
    ]

    fold_count = _resolve_cv_fold_count(y_train)
    logger.info(log_event("catboost_oof_started", cv_folds=fold_count, train_rows=len(X_train)))
    oof_probabilities = np.full(len(X_train), np.nan)
    if fold_count:
        cv = StratifiedKFold(n_splits=fold_count, shuffle=True, random_state=42)
        for train_index, validation_index in cv.split(X_train, y_train):
            fold_model = CatBoostClassifier(
                loss_function="Logloss",
                eval_metric="PRAUC",
                auto_class_weights="Balanced",
                iterations=400,
                learning_rate=0.05,
                depth=6,
                random_seed=42,
                verbose=False,
                allow_writing_files=False,
            )
            fold_model.fit(X_train.iloc[train_index], y_train.iloc[train_index], cat_features=cat_features)
            oof_probabilities[validation_index] = fold_model.predict_proba(X_train.iloc[validation_index])[:, 1]

    diagnostics = {
        "calibration_score_source": "catboost_out_of_fold" if fold_count else "catboost_in_sample_fallback",
        "cv_folds": fold_count,
    }
    logger.info(log_event("catboost_oof_completed", score_source=diagnostics["calibration_score_source"]))
    return oof_probabilities, diagnostics


def _fit_score_calibrator(scores: np.ndarray, y_true: pd.Series) -> tuple[IsotonicRegression | None, dict[str, Any]]:
    valid_mask = ~np.isnan(scores)
    if CALIBRATION_METHOD != "isotonic" or valid_mask.sum() < 10 or y_true.nunique() < 2:
        logger.warning(
            log_event(
                "calibration_skipped",
                method=CALIBRATION_METHOD,
                rows=int(valid_mask.sum()),
                reason="insufficient_oof_scores_or_single_class",
            )
        )
        return None, {
            "method": "none",
            "reason": "insufficient_oof_scores_or_single_class",
        }

    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(scores[valid_mask], y_true.to_numpy()[valid_mask])
    logger.info(log_event("calibration_fitted", method=CALIBRATION_METHOD, rows=int(valid_mask.sum())))
    return calibrator, {
        "method": CALIBRATION_METHOD,
        "fit_row_count": int(valid_mask.sum()),
    }


def _apply_score_calibration(scores: np.ndarray, calibrator: IsotonicRegression | None) -> np.ndarray:
    if calibrator is None:
        return scores
    return np.asarray(calibrator.predict(scores), dtype=float)


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


def _build_feature_percentile_table(frame: pd.DataFrame, stage_config: ModelStageConfig) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for column in stage_config.feature_policy.numeric_feature_columns:
        if column not in frame.columns:
            continue

        series = pd.to_numeric(frame[column], errors="coerce")
        non_null = series.dropna()
        record: dict[str, Any] = {
            "feature_name": column,
            "row_count": int(len(series)),
            "non_null_count": int(non_null.size),
            "missing_rate": float(series.isna().mean()),
            "min": float(non_null.min()) if not non_null.empty else None,
            "max": float(non_null.max()) if not non_null.empty else None,
            "mean": float(non_null.mean()) if not non_null.empty else None,
            "std": float(non_null.std()) if non_null.size > 1 else None,
        }
        for percentile in FEATURE_PERCENTILE_POINTS:
            key = f"p{int(percentile * 100):02d}"
            record[key] = float(non_null.quantile(percentile)) if not non_null.empty else None
        records.append(record)

    return pd.DataFrame(records)


def _calculate_numeric_psi(train_series: pd.Series, test_series: pd.Series) -> float | None:
    train_values = pd.to_numeric(train_series, errors="coerce").dropna()
    test_values = pd.to_numeric(test_series, errors="coerce").dropna()
    if train_values.empty or test_values.empty or train_values.nunique() < 2:
        return None

    quantiles = np.linspace(0, 1, DRIFT_QUANTILE_BINS + 1)
    bins = np.unique(train_values.quantile(quantiles).to_numpy())
    if bins.size < 3:
        return None
    bins[0] = -np.inf
    bins[-1] = np.inf

    train_counts = pd.cut(train_values, bins=bins, include_lowest=True).value_counts(sort=False)
    test_counts = pd.cut(test_values, bins=bins, include_lowest=True).value_counts(sort=False)
    train_pct = train_counts / train_counts.sum()
    test_pct = test_counts / test_counts.sum()
    epsilon = 1e-6
    psi = ((test_pct - train_pct) * np.log((test_pct + epsilon) / (train_pct + epsilon))).sum()
    return float(psi)


def _build_feature_drift_table(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    stage_config: ModelStageConfig,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for column in stage_config.feature_policy.numeric_feature_columns:
        if column not in train_frame.columns or column not in test_frame.columns:
            continue

        train_series = pd.to_numeric(train_frame[column], errors="coerce")
        test_series = pd.to_numeric(test_frame[column], errors="coerce")
        records.append(
            {
                "feature_name": column,
                "train_missing_rate": float(train_series.isna().mean()),
                "test_missing_rate": float(test_series.isna().mean()),
                "missing_rate_delta": float(test_series.isna().mean() - train_series.isna().mean()),
                "train_mean": float(train_series.mean()) if train_series.notna().any() else None,
                "test_mean": float(test_series.mean()) if test_series.notna().any() else None,
                "mean_delta": float(test_series.mean() - train_series.mean())
                if train_series.notna().any() and test_series.notna().any()
                else None,
                "train_p50": float(train_series.quantile(0.50)) if train_series.notna().any() else None,
                "test_p50": float(test_series.quantile(0.50)) if test_series.notna().any() else None,
                "population_stability_index": _calculate_numeric_psi(train_series, test_series),
            }
        )

    return pd.DataFrame(records)


def _select_threshold_policy(threshold_metrics: pd.DataFrame) -> dict[str, Any]:
    if threshold_metrics.empty:
        return {
            "policy": THRESHOLD_SELECTION_POLICY,
            "selected_threshold": ACTION_THRESHOLD,
            "reason": "threshold table is empty; fixed threshold retained",
        }

    fixed_row = threshold_metrics.iloc[(threshold_metrics["threshold"] - ACTION_THRESHOLD).abs().argsort()[:1]]
    capacity_rows = threshold_metrics.loc[threshold_metrics["actioned_count"] <= OPERATIONAL_ACTION_CAPACITY]
    capacity_threshold = None
    if not capacity_rows.empty:
        capacity_threshold = float(capacity_rows.sort_values(["recall", "precision"], ascending=False).iloc[0]["threshold"])

    return {
        "policy": THRESHOLD_SELECTION_POLICY,
        "selected_threshold": ACTION_THRESHOLD,
        "fixed_threshold_metrics": dataframe_to_json_records(fixed_row)[0],
        "operational_action_capacity": OPERATIONAL_ACTION_CAPACITY,
        "capacity_feasible_threshold": capacity_threshold,
        "reason": "fixed ACTION_THRESHOLD is retained; capacity threshold is reported as decision support",
    }


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

    logger.info(
        log_event(
            "training_pipeline_started",
            model_stage=stage_config.stage.value,
            train_rows=len(split_bundle.train_df),
            test_rows=len(split_bundle.test_df),
            run_dir=run_dir,
        )
    )
    logistic_model, logistic_train_probabilities, logistic_probabilities, feeder_diagnostics = _train_logistic_regression(
        split_bundle,
        stage_config,
    )
    logistic_model_path = models_dir / "logistic_regression_feeder.joblib"
    joblib.dump(logistic_model, logistic_model_path)

    stacked_split_bundle = TemporalSplitBundle(
        train_df=split_bundle.train_df.assign(logistic_regression_score=logistic_train_probabilities),
        test_df=split_bundle.test_df.assign(logistic_regression_score=logistic_probabilities),
        split_year_column=split_bundle.split_year_column,
    )
    catboost_oof_probabilities, calibration_score_diagnostics = _train_catboost_oof_predictions(
        stacked_split_bundle,
        stage_config,
    )
    catboost_model, catboost_train_probabilities, catboost_probabilities = _train_catboost(stacked_split_bundle, stage_config)
    y_train = stacked_split_bundle.train_df["no_show_flag"].astype(int)
    if np.isnan(catboost_oof_probabilities).any():
        catboost_oof_probabilities = catboost_train_probabilities
    calibrator, calibration_diagnostics = _fit_score_calibrator(catboost_oof_probabilities, y_train)
    calibrated_catboost_probabilities = _apply_score_calibration(catboost_probabilities, calibrator)
    catboost_model_path = models_dir / "catboost_with_logistic_score.cbm"
    calibrator_path = models_dir / "catboost_probability_calibrator.joblib"
    catboost_model.save_model(str(catboost_model_path))
    if calibrator is not None:
        joblib.dump(calibrator, calibrator_path)

    model_artifacts = {
        "catboost_with_logistic_score": _evaluate_model(
            split_bundle=split_bundle,
            probabilities=calibrated_catboost_probabilities,
            model_name="catboost_with_logistic_score",
            model_version=f"catboost_logreg_stack_{timestamp}",
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

    comparison_df = pd.DataFrame(comparison_records).sort_values(["f1", "pr_auc", "roc_auc"], ascending=False)
    recommended_model = comparison_df.iloc[0]["model_name"]

    feature_list_path = reports_dir / "feature_list.json"
    risk_thresholds_path = reports_dir / "risk_thresholds.json"
    feature_percentiles_path = reports_dir / "feature_percentiles.csv"
    feature_drift_path = reports_dir / "feature_drift.csv"
    threshold_policy_path = reports_dir / "threshold_policy.json"
    stacking_summary_path = reports_dir / "stacking_summary.json"
    import_summary_path = reports_dir / "import_summary.json"
    split_summary_path = reports_dir / "split_summary.json"
    comparison_table_path = reports_dir / "model_comparison.csv"
    evaluation_summary_path = reports_dir / "evaluation_summary.json"
    clean_dataset_path = datasets_dir / "reservations_clean.csv"
    feature_dataset_path = datasets_dir / "reservation_features.csv"

    write_json(feature_list_path, stage_config.feature_policy.to_machine_readable_dict() | {"model_stage": stage_config.stage.value})
    write_json(
        risk_thresholds_path,
        {
            "action_threshold": ACTION_THRESHOLD,
            "risk_class_bands": list(RISK_CLASS_BANDS),
            "score_definition": "score = raw model probability for no-show",
            "note": "Bands are evaluated from top to bottom; first matching minimum_score wins.",
        },
    )
    feature_percentiles = pd.concat(
        [
            _build_feature_percentile_table(split_bundle.train_df, stage_config).assign(split_name="train"),
            _build_feature_percentile_table(split_bundle.test_df, stage_config).assign(split_name="test"),
        ],
        ignore_index=True,
    )
    write_dataframe(feature_percentiles, feature_percentiles_path)
    write_dataframe(_build_feature_drift_table(split_bundle.train_df, split_bundle.test_df, stage_config), feature_drift_path)
    primary_artifact = next(iter(model_artifacts.values()))
    write_json(threshold_policy_path, _select_threshold_policy(primary_artifact.threshold_metrics))
    write_json(
        stacking_summary_path,
        {
            "feeder": feeder_diagnostics,
            "catboost_oof": calibration_score_diagnostics,
            "calibration": calibration_diagnostics,
            "raw_catboost_train_score_summary": {
                "mean": float(np.mean(catboost_train_probabilities)),
                "std": float(np.std(catboost_train_probabilities)),
            },
            "calibrated_test_score_summary": {
                "mean": float(np.mean(calibrated_catboost_probabilities)),
                "std": float(np.std(calibrated_catboost_probabilities)),
            },
        },
    )
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
                    "calibrator_path": str(calibrator_path) if calibrator is not None else None,
                    "feeder_model": {
                        "model_name": "logistic_regression",
                        "model_path": str(logistic_model_path),
                        "feature_name": "logistic_regression_score",
                        "score_source": feeder_diagnostics["stacking_score_source"],
                    },
                    "calibration": calibration_diagnostics,
                }
                for model_name, artifact in model_artifacts.items()
            },
        },
    )

    refresh_latest_artifacts(run_dir, latest_dir)
    logger.info(
        log_event(
            "artifacts_written",
            reports_dir=reports_dir,
            models_dir=models_dir,
            predictions_dir=predictions_dir,
            recommended_model=recommended_model,
        )
    )
    logger.info(log_event("training_pipeline_completed", model_stage=stage_config.stage.value, run_dir=run_dir))

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

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.training.stages import ModelStageConfig


@dataclass
class DatasetBundle:
    raw_df: pd.DataFrame
    clean_df: pd.DataFrame
    feature_df: pd.DataFrame
    modeling_df: pd.DataFrame
    import_summary: dict[str, Any]
    stage_config: ModelStageConfig


@dataclass
class TemporalSplitBundle:
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    split_year_column: str


@dataclass
class ModelRunArtifacts:
    model_name: str
    model_version: str
    metrics: dict[str, Any]
    threshold_metrics: pd.DataFrame
    top_k_metrics: pd.DataFrame
    calibration_table: pd.DataFrame
    predictions: pd.DataFrame
    model_path: Path


@dataclass
class TrainingRunArtifacts:
    model_stage: str
    run_dir: Path
    latest_dir: Path
    feature_list_path: Path
    import_summary_path: Path
    clean_dataset_path: Path
    feature_dataset_path: Path
    split_summary_path: Path
    comparison_table_path: Path
    evaluation_summary_path: Path
    prediction_paths: dict[str, Path]
    model_paths: dict[str, Path]
    persistence_summary_path: Path | None = None

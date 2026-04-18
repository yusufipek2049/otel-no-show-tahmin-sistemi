from __future__ import annotations

import argparse
from pathlib import Path

from app.training.constants import DEFAULT_ARTIFACTS_ROOT, DEFAULT_DATA_DIR
from app.training.features import build_dataset_bundle
from app.training.ingestion import load_raw_reservation_data, load_reservation_snapshot_data
from app.training.persistence import persist_training_outputs_to_database, write_json
from app.training.pipeline import run_training_pipeline
from app.training.split import temporal_train_test_split
from app.training.stages import ModelStage, ensure_snapshot_support, get_model_stage_config, list_model_stage_names, resolve_output_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train no-show models for booking-time or later snapshot-based stages.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Directory containing H1.csv and H2.csv.")
    parser.add_argument(
        "--model-stage",
        type=str,
        default=ModelStage.BOOKING_TIME.value,
        choices=list_model_stage_names(),
        help="Model stage to train. Booking-time uses H1/H2; later stages require a snapshot CSV.",
    )
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=None,
        help="CSV path for stage-aware reservation snapshots. Required for post-booking stages.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_ARTIFACTS_ROOT,
        help="Base directory where training artifacts will be written.",
    )
    parser.add_argument(
        "--download-if-missing",
        action="store_true",
        help="Download the public H1/H2 files into the data directory if they are missing.",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Optional SQLAlchemy database URL. If provided, raw/clean/features/predictions are persisted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stage_config = get_model_stage_config(args.model_stage)
    ensure_snapshot_support(stage_config, args.snapshot_path)

    if stage_config.requires_snapshot_data:
        source_df = load_reservation_snapshot_data(args.snapshot_path)
    else:
        source_df = load_raw_reservation_data(args.data_dir, download_if_missing=args.download_if_missing)

    dataset_bundle = build_dataset_bundle(source_df, model_stage=stage_config.stage)
    split_bundle = temporal_train_test_split(dataset_bundle.modeling_df, stage_config=stage_config)
    output_root = resolve_output_root(args.output_dir, stage_config)
    training_artifacts, model_artifacts = run_training_pipeline(
        raw_df=dataset_bundle.raw_df,
        clean_df=dataset_bundle.clean_df,
        feature_df=dataset_bundle.feature_df,
        split_bundle=split_bundle,
        import_summary=dataset_bundle.import_summary,
        stage_config=stage_config,
        output_root=output_root,
    )

    if args.database_url:
        if stage_config.requires_snapshot_data:
            raise NotImplementedError(
                "Snapshot-stage database persistence is not implemented yet. "
                "Persist the stage artifacts first, then extend the schema with snapshot tables."
            )

        persistence_summary = persist_training_outputs_to_database(
            args.database_url,
            raw_df=dataset_bundle.raw_df,
            clean_df=dataset_bundle.clean_df,
            feature_df=dataset_bundle.feature_df,
            prediction_frames={name: artifact.predictions for name, artifact in model_artifacts.items()},
            feature_set_version=stage_config.feature_set_version,
        )
        persistence_summary_path = training_artifacts.run_dir / "reports" / "database_persistence_summary.json"
        write_json(persistence_summary_path, persistence_summary)
        write_json(training_artifacts.latest_dir / "reports" / "database_persistence_summary.json", persistence_summary)

    print(f"Model stage: {stage_config.stage.value}")
    print(f"Training artifacts written to: {training_artifacts.run_dir}")
    print(f"Latest artifact alias refreshed at: {training_artifacts.latest_dir}")
    print(f"Evaluation summary: {training_artifacts.evaluation_summary_path}")


if __name__ == "__main__":
    main()

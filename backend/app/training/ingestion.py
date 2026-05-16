from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from app.training.constants import DEFAULT_DATA_DIR, RAW_DATA_URLS

ALLOWED_DOWNLOAD_HOSTS = {"raw.githubusercontent.com"}


def _validate_public_data_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError(f"Unsupported public data URL: {url}")


def download_public_hotel_booking_data(
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: dict[str, Path] = {}

    for filename, url in RAW_DATA_URLS.items():
        target_path = data_dir / filename
        if overwrite or not target_path.exists():
            _validate_public_data_url(url)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            target_path.write_bytes(response.content)
        downloaded_files[filename] = target_path

    return downloaded_files


def resolve_data_files(
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    download_if_missing: bool = False,
) -> dict[str, Path]:
    resolved = {filename: data_dir / filename for filename in RAW_DATA_URLS}
    missing = [filename for filename, path in resolved.items() if not path.exists()]

    if missing and download_if_missing:
        return download_public_hotel_booking_data(data_dir)

    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required source files in {data_dir}: {missing_str}. "
            "Pass download_if_missing=True or place the files there manually."
        )

    return resolved


def load_raw_reservation_data(
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    download_if_missing: bool = False,
) -> pd.DataFrame:
    data_files = resolve_data_files(data_dir, download_if_missing=download_if_missing)
    frames: list[pd.DataFrame] = []

    for filename, file_path in sorted(data_files.items()):
        frame = pd.read_csv(file_path, dtype="string", keep_default_na=False)
        frame["source_file"] = filename
        frame["source_row_number"] = range(1, len(frame) + 1)
        frame["reservation_key"] = frame["source_file"] + ":" + frame["source_row_number"].astype("string")
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def load_reservation_snapshot_data(snapshot_path: Path) -> pd.DataFrame:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot dataset was not found: {snapshot_path}")
    return pd.read_csv(snapshot_path, dtype="string", keep_default_na=False)

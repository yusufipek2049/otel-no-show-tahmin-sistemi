from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.core.logging import log_event, mask_database_url
from app.main import app


def test_log_event_formats_key_value_fields() -> None:
    assert log_event("request_completed", method="GET", path="/api/v1/health", status_code=200) == (
        "request_completed method=GET path=/api/v1/health status_code=200"
    )


def test_mask_database_url_removes_credentials() -> None:
    masked = mask_database_url("postgresql+psycopg://postgres:secret@localhost:5432/hotel_no_show")

    assert masked == "postgresql+psycopg://localhost:5432/hotel_no_show"
    assert "secret" not in masked


def test_request_logging_middleware_logs_completed_request(caplog) -> None:
    caplog.set_level(logging.INFO)
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert any("request_completed method=GET path=/api/v1/health status_code=200" in record.message for record in caplog.records)

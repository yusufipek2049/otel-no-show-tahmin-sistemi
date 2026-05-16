from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_reports_benchmark_endpoint_smoke() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/reports/benchmark")

    assert response.status_code == 200
    payload = response.json()
    assert "primary_metrics" in payload
    assert "models" in payload
    assert "comparison" in payload


def test_reports_operations_summary_endpoint_smoke() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/reports/operations-summary")

    assert response.status_code == 200
    payload = response.json()
    assert "total_reservations" in payload
    assert "data_source" in payload


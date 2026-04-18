from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary_returns_response() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert "kpis" in response.json()
    assert "items" in response.json()


def test_reservations_returns_response() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/reservations")

    assert response.status_code == 200
    assert "items" in response.json()
    assert "filters" in response.json()

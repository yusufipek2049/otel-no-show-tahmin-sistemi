from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.prediction import Prediction
from app.models.reservation import ReservationClean, ReservationImportBatch, ReservationRaw


@pytest.fixture()
def client_with_sqlite_db() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        batch = ReservationImportBatch(source_name="test", source_files=["H1.csv"], status="complete", row_count=1)
        db.add(batch)
        db.flush()

        raw = ReservationRaw(
            batch_id=batch.id,
            source_file="H1.csv",
            source_row_number=1,
            property_code="RESORT_H1",
            raw_payload={"ReservationStatus": "Check-Out"},
            reservation_status="Check-Out",
        )
        db.add(raw)
        db.flush()

        clean = ReservationClean(
            raw_reservation_id=raw.id,
            batch_id=batch.id,
            property_id="RESORT_H1",
            source_file="H1.csv",
            arrival_date=date(2017, 7, 1),
            arrival_year=2017,
            no_show_flag=False,
            excluded_from_training=False,
        )
        db.add(clean)
        db.flush()

        prediction = Prediction(
            reservation_clean_id=clean.id,
            model_name="catboost_with_logistic_score",
            model_version="test-version",
            score=0.82,
            risk_class="high",
            threshold_used=0.40,
            scoring_run_id="test-run",
        )
        db.add(prediction)
        db.commit()

    def override_get_db() -> Iterator[Session]:
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def test_create_list_and_update_reservation_action(client_with_sqlite_db: TestClient) -> None:
    create_response = client_with_sqlite_db.post(
        "/api/v1/reservations/1/actions",
        json={
            "action_type": "call_guest",
            "action_status": "open",
            "action_note": "Misafir aranacak.",
            "acted_by": "operations",
            "payload": {"channel": "phone"},
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["reservation_id"] == 1
    assert created["prediction_id"] == 1
    assert created["action_type"] == "call_guest"
    assert created["action_status"] == "open"

    list_response = client_with_sqlite_db.get("/api/v1/reservations/1/actions")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client_with_sqlite_db.patch(
        f"/api/v1/actions/{created['id']}",
        json={"action_status": "completed", "action_note": "Misafir teyit verdi."},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["action_status"] == "completed"
    assert updated["action_note"] == "Misafir teyit verdi."


def test_create_reservation_action_returns_404_for_missing_reservation(client_with_sqlite_db: TestClient) -> None:
    response = client_with_sqlite_db.post(
        "/api/v1/reservations/999/actions",
        json={
            "action_type": "call_guest",
            "action_status": "open",
            "acted_by": "operations",
        },
    )

    assert response.status_code == 404

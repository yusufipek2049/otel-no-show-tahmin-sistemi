# Hotel No-Show Prediction and Operations Dashboard

This repository is an end-to-end hotel no-show prediction system. It covers leakage-safe feature engineering, temporal validation, calibrated risk scoring, threshold and Top-K evaluation, DB-backed prediction persistence, artifact fallback views, model documentation, tests, CI, and an operations dashboard.

The project is built as an applied ML engineering system. Model training is connected to the day-to-day workflow where hotel teams review risky reservations and record follow-up actions.

## Project Purpose

Hotels lose capacity and revenue when guests do not arrive without canceling. A useful no-show system needs to do more than train a classifier. It needs auditable risk scores, a clear data availability policy, operational thresholds, persisted predictions, and workflows that staff can actually use.

This repository implements that path:

- FastAPI backend
- PostgreSQL schema and Alembic migration
- training pipeline with artifact generation
- DB-backed prediction store
- artifact fallback mode for local demos
- Next.js operations dashboard
- reservation detail and action workflow
- management reports
- model card, dataset card, and research-style documentation

## Problem Definition

The primary ML task is binary no-show prediction:

- positive class: `ReservationStatus == "No-Show"`
- negative class: `ReservationStatus == "Check-Out"`
- excluded from no-show training: `ReservationStatus == "Canceled"`

Canceled reservations are a different business outcome and should be modeled separately if needed.

The active stages are:

- `customer_pre_reservation`: customer-level no-show propensity before a specific reservation is finalized
- `reservation_post_booking`: reservation-level no-show risk after a booking exists

The legacy `booking_time` stage is still kept for compatibility and leakage-safe baseline work.

## Why It Matters

No-show prediction is valuable only when it supports a concrete action:

- contact the guest
- verify guarantee or deposit details
- prioritize manual review
- manage overbooking risk
- measure action coverage and outcomes

For that reason, the project evaluates not only ranking metrics, but also threshold behavior, action volume, Top-K capture, calibration, and prediction-store persistence.

## Current Model Decision

Active final model architecture:

- `catboost_with_logistic_score`

Logistic Regression is not presented as a separate production candidate. It is used as an internal feeder:

- train a Logistic Regression feeder
- generate `logistic_regression_score`
- pass that score into CatBoost
- calibrate CatBoost probabilities with isotonic regression

Score semantics:

- score is direct no-show probability
- higher score means higher no-show risk
- do not use `1.0 - score`

Current threshold policy:

- action threshold: `0.90`
- high risk: `>= 0.80`
- medium risk: `>= 0.67`
- notable risk: `>= 0.50`
- low risk: `< 0.50`

## Architecture

```text
.
├── backend
│   ├── alembic
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── jobs
│   │   ├── models
│   │   ├── repositories
│   │   ├── schemas
│   │   ├── services
│   │   └── training
│   └── tests
├── data
├── docs
├── frontend
│   ├── app
│   ├── components
│   └── lib
├── .github
│   └── workflows
└── docker-compose.yml
```

## Backend Structure

- `app/api`: FastAPI route definitions
- `app/core`: configuration and shared infrastructure
- `app/db`: SQLAlchemy session and base setup
- `app/models`: ORM models
- `app/repositories`: data access and artifact views
- `app/schemas`: Pydantic response/request contracts
- `app/services`: application workflow orchestration
- `app/training`: ingestion, feature engineering, split, evaluation, model training, and persistence
- `app/jobs/train_booking_time_no_show.py`: CLI training entrypoint

## Frontend Structure

- `frontend/app/dashboard`: operations summary and risky reservation queue
- `frontend/app/customer-risk`: customer-level pre-reservation risk view
- `frontend/app/reservation-risk`: post-booking reservation risk view
- `frontend/app/reservations`: filterable reservation queue
- `frontend/app/reservations/[reservationId]`: reservation detail and action workflow
- `frontend/app/reports`: management and model quality reports
- `frontend/components`: shared UI components
- `frontend/lib`: API client, types, and presentation helpers

## Training Pipeline

The training pipeline:

1. Loads raw reservation data.
2. Normalizes strings and null-like values.
3. Builds clean reservation records.
4. Constructs the no-show target.
5. Excludes canceled rows from no-show training.
6. Builds stage-specific features.
7. Applies leakage guards.
8. Uses a temporal train/test split.
9. Trains the Logistic Regression feeder.
10. Trains CatBoost with the feeder score.
11. Applies isotonic calibration.
12. Writes model, prediction, and report artifacts.

Key files:

- `backend/app/training/ingestion.py`
- `backend/app/training/features.py`
- `backend/app/training/stages.py`
- `backend/app/training/split.py`
- `backend/app/training/evaluation.py`
- `backend/app/training/pipeline.py`
- `backend/app/training/persistence.py`

## Leakage Policy

Hard exclusions:

- `ReservationStatus`
- `ReservationStatusDate`
- `IsCanceled`
- `no_show_flag`

Canceled rows are excluded from the binary no-show training dataset.

Final-state operational fields must not be used for earlier scoring cutoffs unless they are available as timestamped as-of features.

Detailed policy:

- `docs/feature-policy.md`
- `docs/data-mapping.md`
- `docs/dataset-card.md`

## Evaluation Methodology

Random split is not used for headline model quality claims.

Current temporal split:

- train: 2015-2016
- test: 2017

Primary evaluation outputs are generated after a training run:

- PR-AUC
- ROC-AUC
- precision / recall / F1 at threshold
- actioned count
- recall at Top-K
- Brier score
- calibration table
- feature percentiles
- feature drift report
- threshold policy report
- stacking summary

Generated files are written under each stage's artifact directory.

## Database-Backed Prediction Store

The database schema supports:

- raw imports
- clean reservations
- reservation features
- predictions
- reservation actions
- audit logs

If prediction rows exist in the database, the app uses the DB-backed prediction store as the primary source for operational screens.

## Artifact Fallback Mode

If the database does not contain persisted predictions, the app can read the latest training artifacts directly.

Default operational fallback:

- `backend/artifacts/booking_time_no_show/reservation_post_booking/latest`

This mode is useful for local demos and model inspection, but it is read-only for action analytics.

## Local Setup

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Create backend environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend defaults:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default:

- `http://localhost:3000`

Environment variable used by the frontend:

- `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000/api/v1`

## Train Models

The script downloads the public H1/H2 CSVs when `--download-if-missing` is provided and local files are absent.

Train the customer-level stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage customer_pre_reservation \
  --download-if-missing
```

Train the reservation-level stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing
```

Persist reservation-stage predictions to PostgreSQL:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

## Artifacts

Active stage artifacts:

- `backend/artifacts/booking_time_no_show/customer_pre_reservation/latest/`
- `backend/artifacts/booking_time_no_show/reservation_post_booking/latest/`

Typical outputs:

- `datasets/reservations_clean.csv`
- `datasets/reservation_features.csv`
- `models/catboost_with_logistic_score.cbm`
- `models/logistic_regression_feeder.joblib`
- `models/catboost_probability_calibrator.joblib`
- `predictions/catboost_with_logistic_score_predictions.csv`
- `reports/evaluation_summary.json`
- `reports/model_comparison.csv`
- `reports/*_threshold_metrics.csv`
- `reports/*_top_k_metrics.csv`
- `reports/*_calibration.csv`
- `reports/feature_percentiles.csv`
- `reports/feature_drift.csv`
- `reports/risk_thresholds.json`
- `reports/threshold_policy.json`
- `reports/stacking_summary.json`

## Main API Endpoints

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/reservations`
- `GET /api/v1/reservations/{reservation_id}`
- `GET /api/v1/reservations/{reservation_id}/actions`
- `POST /api/v1/reservations/{reservation_id}/actions`
- `PATCH /api/v1/actions/{action_id}`
- `GET /api/v1/reports/benchmark`
- `GET /api/v1/reports/benchmark?stage=customer_pre_reservation`
- `GET /api/v1/reports/benchmark?stage=reservation_post_booking`
- `GET /api/v1/reports/operations-summary`
- `GET /api/v1/reports/no-show-trends`
- `GET /api/v1/reports/channel-breakdown`
- `GET /api/v1/reports/segment-breakdown`
- `GET /api/v1/reports/action-effectiveness`

## Frontend Routes

- `/dashboard`
- `/customer-risk`
- `/reservation-risk`
- `/reservations`
- `/reservations/[reservationId]`
- `/reports`

## Tests And CI

Backend:

```bash
cd backend
pytest
python3 -m compileall app
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
```

CI:

- `.github/workflows/ci.yml`

The CI workflow installs backend and frontend dependencies, runs backend tests, compiles backend modules, type-checks the frontend, and builds the Next.js app.

## Documentation

- `docs/research-report.md`
- `docs/model-training-decision-record.md`
- `docs/model-card.md`
- `docs/dataset-card.md`
- `docs/modeling-plan.md`
- `docs/feature-policy.md`
- `docs/evaluation.md`
- `docs/model-tierlist.md`
- `docs/data-mapping.md`
- `docs/v1-v2-gap-analysis.md`
- `docs/acceptance-criteria.md`

## Limitations

- The public H1/H2 dataset is a final-state extract, not a full event log.
- Payment failure, contact history, campaign, and guarantee/deposit signals are synthetic proxies in the proof-of-concept.
- Production use requires timestamped PMS, CRM, payment, campaign, and action outcome data.
- Auth and role-based access are not complete.
- Artifact fallback is useful for demos but should not replace DB-backed scoring in production.
- Current metrics should be read from generated artifacts after a training run; this README intentionally avoids hard-coded metric claims.

## Roadmap

1. Replace synthetic operational signals with real timestamped source data.
2. Add a dedicated batch/live scoring job separate from training.
3. Persist active stage predictions to the database by default.
4. Add role-based access control.
5. Track action outcomes, not only action status.
6. Add drift, calibration, and threshold monitoring over time.
7. Add deeper period-over-period management reports.

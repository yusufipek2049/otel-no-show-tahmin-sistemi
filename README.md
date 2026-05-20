# Hotel Arrival Risk Prediction and Operations Dashboard

Predict hotel arrival failure risk and turn risky reservations into an operations dashboard with follow-up queues, reports, charts, and action tracking.

This project is an end-to-end ML + web application for hotel operations teams. It keeps pure no-show prediction separate from the broader **arrival failure** view, where both `Canceled` and `No-Show` reservations are treated as reservations that did not become completed stays.

## What It Does

- Trains leakage-aware hotel reservation risk models.
- Uses temporal validation instead of random split for headline results.
- Produces calibrated risk scores with threshold and fixed-list capture reports.
- Shows risky reservations in a hotel-staff-friendly dashboard.
- Provides a filterable call and follow-up pool.
- Lets staff record calls, messages, deposit checks, and follow-up notes.
- Shows management reports with trend, channel-risk, and list-size capture charts.
- Runs from PostgreSQL predictions when available, or from latest artifacts in local demo mode.

## Current Product Direction

The main operational screen now focuses on `arrival_failure_post_booking`:

- positive: `ReservationStatus` in `Canceled`, `No-Show`
- negative: `ReservationStatus == "Check-Out"`

Pure no-show is still supported as a stricter technical view:

- positive: `ReservationStatus == "No-Show"`
- negative: `ReservationStatus == "Check-Out"`
- excluded from pure no-show training: `ReservationStatus == "Canceled"`

Active stages:

- `customer_pre_reservation`: customer-level pre-check before a specific reservation is finalized
- `reservation_post_booking`: narrow reservation-level no-show risk
- `arrival_failure_post_booking`: main reservation-level arrival failure risk

## Model Decision

The active final model is:

- `catboost_with_logistic_score`

Logistic Regression is used as an internal feeder. Its score is passed into CatBoost, then CatBoost probabilities are calibrated with isotonic regression.

Current threshold policy:

- action threshold: `0.40`
- high risk: `>= 0.80`
- medium risk: `>= 0.67`
- notable risk: `>= 0.50`
- low risk: `< 0.50`

Scores are direct positive-class probabilities for the selected stage. Do not invert them.

## Application Routes

Frontend:

- `/dashboard`: daily follow-up summary for hotel staff
- `/reservations`: call and follow-up pool
- `/reservations/[reservationId]`: reservation detail and follow-up history
- `/reports`: management reports and charts
- `/customer-risk`: customer pre-check view
- `/reservation-risk`: pure no-show technical view

Backend API:

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/reservations`
- `GET /api/v1/reservations/{reservation_id}`
- `GET /api/v1/reservations/{reservation_id}/actions`
- `POST /api/v1/reservations/{reservation_id}/actions`
- `PATCH /api/v1/actions/{action_id}`
- `GET /api/v1/reports/benchmark`
- `GET /api/v1/reports/operations-summary`
- `GET /api/v1/reports/no-show-trends`
- `GET /api/v1/reports/channel-breakdown`
- `GET /api/v1/reports/segment-breakdown`
- `GET /api/v1/reports/action-effectiveness`

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
└── docker-compose.yml
```

## Local Setup

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Useful URLs:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Train Models

Train the main arrival failure stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage arrival_failure_post_booking \
  --download-if-missing
```

Train the pure no-show stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing
```

Train the customer pre-check stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage customer_pre_reservation \
  --download-if-missing
```

Persist predictions to PostgreSQL:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage arrival_failure_post_booking \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

Latest local artifact fallback:

- `backend/artifacts/booking_time_no_show/arrival_failure_post_booking/latest`

## Test And Quality Commands

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

Static/security checks used during review:

```bash
ruff check backend
mypy backend/app --ignore-missing-imports
bandit -r backend/app -x backend/tests
semgrep scan --config auto .
pip-audit -l
```

Latest backend dynamic test result during this pass:

- `36 passed`

## Consolidated Documentation

The documentation was merged to reduce duplication:

- `docs/ml-system-guide.md`: data, targets, leakage policy, model design, evaluation, artifacts, and limitations
- `docs/product-guide.md`: demo flow, product surfaces, acceptance criteria, backlog, and roadmap
- `docs/quality-and-testing.md`: dynamic tests, static analysis, security checks, and software engineering notes

## Limitations

- Public H1/H2 data is a final-state extract, not a full event log.
- Payment, contact, campaign, guarantee, and deposit signals are synthetic proxies in this proof-of-concept.
- Arrival failure metrics are not pure no-show metrics; cancellations are much more common than no-shows.
- Production use requires timestamped PMS, CRM, payment, campaign, and action outcome data.
- Authentication and role-based access are not complete.
- Artifact fallback is useful for demos, but production should use persisted database predictions.

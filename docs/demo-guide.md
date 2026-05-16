# Demo Guide

This guide walks through a local demo of the hotel no-show prediction and operations dashboard.

## Start The Backend

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Install backend dependencies and run migrations:

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
- health check: `http://localhost:8000/api/v1/health`

## Start The Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default:

- `http://localhost:3000`

If the backend runs somewhere else, set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Run Training

Train the customer-level pre-reservation stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage customer_pre_reservation \
  --download-if-missing
```

Train the reservation-level post-booking stage:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing
```

Training writes stage-specific artifacts under:

- `backend/artifacts/booking_time_no_show/customer_pre_reservation/latest/`
- `backend/artifacts/booking_time_no_show/reservation_post_booking/latest/`

## Populate The DB Prediction Store

To persist reservation-stage predictions to PostgreSQL:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

When prediction rows exist in the database, the app reads operational queues from the DB-backed prediction store. When they do not, it reads the latest artifacts in read-only fallback mode.

## Screens To Show

A clear demo flow is:

1. `/dashboard`
2. `/reservation-risk`
3. `/reservations`
4. `/reservations/[reservationId]`
5. `/customer-risk`
6. `/reports`
7. Swagger: `/docs`

What each screen shows:

- `/dashboard`: operational queue and high-risk reservation summary
- `/reservation-risk`: reservation-level model quality and threshold behavior
- `/reservations`: filterable reservation queue
- `/reservations/[reservationId]`: reservation context and staff action workflow
- `/customer-risk`: customer-level pre-reservation risk view
- `/reports`: management reporting, benchmark summary, and action effectiveness
- `/docs`: API structure and backend surface area

## Suggested 3-Minute Demo Script

**0:00-0:25 Problem**

Hotels need to find high-risk reservations before those reservations turn into no-shows. This system turns prediction into an operations queue instead of leaving it as a notebook model.

**0:25-0:55 Training**

The training pipeline builds leakage-safe features, excludes canceled reservations from the no-show target, and uses a temporal split: 2015-2016 for training and 2017 for testing. The active model is CatBoost with a Logistic Regression feeder score and isotonic calibration.

**0:55-1:20 Evaluation**

Evaluation focuses on rare-event and operations metrics: PR-AUC, threshold precision and recall, Top-K capture, calibration, Brier score, and action volume. Scores are direct no-show probabilities.

**1:20-1:45 Serving**

Predictions can be persisted to PostgreSQL. When the store is populated, the application serves risk queues from the database. For local demos, the same screens can read latest training artifacts as a fallback.

**1:45-2:15 Dashboard**

The operations team reviews high-risk reservations, sees the current scoring source, and uses filters plus detail pages to decide what needs attention first.

**2:15-2:40 Actions**

Staff can record interventions such as calls, messages, deposit requests, or manual review. That connects model output to an auditable workflow.

**2:40-3:00 Reports**

The reports page shows model quality, threshold behavior, Top-K capture, no-show trends, channel and segment breakdowns, and action effectiveness summaries. It closes the loop between training and operations.

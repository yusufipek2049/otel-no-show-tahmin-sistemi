# Demo Guide

This guide is for a short local demo of the hotel no-show prediction system for a recruiter, interviewer, or technical reviewer.

## 1. Demo Goal

In 3-5 minutes, show the full product loop:

- train a leakage-aware no-show model
- generate model artifacts and evaluation reports
- optionally persist predictions to PostgreSQL
- review risky reservations in the dashboard
- record operational actions and inspect reports

Do not quote fixed metric values during the demo. Metrics are generated under `backend/artifacts/` after each training run.

## 2. Prerequisites

- Docker and Docker Compose
- Python 3.10 or newer
- Node.js and npm
- Local CSV files in `data/`, or internet access to use `--download-if-missing`

## 3. Start PostgreSQL

From the repository root:

```bash
docker compose up -d postgres
```

Default database connection:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show
```

## 4. Run Backend

In a separate terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Useful URLs:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- health check: `http://localhost:8000/api/v1/health`

## 5. Run Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend defaults to `http://localhost:8000/api/v1`. If needed, set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## 6. Run Training Pipeline

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

Artifacts are written under:

- `backend/artifacts/booking_time_no_show/customer_pre_reservation/latest/`
- `backend/artifacts/booking_time_no_show/reservation_post_booking/latest/`

Evaluation metrics, threshold tables, calibration outputs, predictions, and model files are generated in those artifact directories.

## 7. Persist Predictions To The Database

To populate PostgreSQL from a training run:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage reservation_post_booking \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

When database predictions exist, operational API views use the prediction store. If the database is empty, the app can still use the latest artifacts as a local read-only fallback.

## 8. Pages To Show

Recommended order:

1. `/dashboard`: operational summary and high-risk queue
2. `/reservation-risk`: reservation-stage model quality and threshold behavior
3. `/reservations`: filterable reservation list
4. `/reservations/[reservationId]`: reservation detail and action logging
5. `/customer-risk`: customer-level pre-reservation risk view
6. `/reports`: model, business, segment, and action reports
7. `http://localhost:8000/docs`: API surface

## 9. Three-Minute Demo Script

**0:00-0:30 - Problem and scope**

This project predicts hotel no-shows and turns those predictions into an operations workflow. The target is binary no-show prediction: no-show versus check-out, with canceled reservations excluded from training.

**0:30-1:00 - Training**

The training pipeline imports hotel booking data, cleans reservation records, applies feature policy checks, uses a temporal split, trains the active model, and writes artifacts under `backend/artifacts/`.

**1:00-1:30 - Evaluation**

Open the risk or reports page. Explain that the demo does not hard-code metrics; PR-AUC, recall, precision, F1, threshold analysis, calibration, and Top-K outputs are generated after training.

**1:30-2:15 - Operations dashboard**

Show `/dashboard`, then `/reservations`. Explain how risky reservations are surfaced for review and how the system can run from persisted DB predictions or local artifact fallback.

**2:15-2:45 - Action workflow**

Open a reservation detail page and show the action panel. The point is auditability: staff actions such as calls, messages, or manual review are recorded instead of leaving model output disconnected from operations.

**2:45-3:00 - Wrap-up**

Show `/reports` and Swagger. Close by explaining that the project connects model training, persistence, APIs, dashboard review, action logging, and reporting in one local system.

## 10. Common Troubleshooting

- **PostgreSQL will not start:** check whether port `5432` is already in use, or set `POSTGRES_PORT` before running Docker Compose.
- **Backend cannot connect to the database:** confirm `docker compose ps` shows Postgres running, then rerun `alembic upgrade head` from `backend/`.
- **Frontend cannot load data:** make sure the backend is running on `localhost:8000` and `NEXT_PUBLIC_API_BASE_URL` points to `/api/v1`.
- **Training cannot find data:** place `H1.csv` and `H2.csv` in `data/`, or run with `--download-if-missing`.
- **Metrics are missing:** run the training pipeline first. Metrics and reports are generated under the relevant `backend/artifacts/.../latest/reports/` directory.
- **Dashboard has no DB-backed predictions:** run the persistence command in section 7, or use artifact fallback mode for a local read-only demo.

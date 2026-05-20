# Product Guide

This guide replaces the previous separate demo, acceptance, backlog, and V1/V2 documents.

## Product Goal

The product helps hotel staff decide which reservations should be contacted or reviewed before arrival. The interface should not feel like a model lab. It should show a daily follow-up pool, explain why the list matters, and let the team record what they did.

## Main Screens

- `/dashboard`: daily follow-up summary and high-priority reservations
- `/reservations`: filterable call and follow-up pool
- `/reservations/[reservationId]`: reservation context, suggested follow-up, and action history
- `/reports`: management charts and operational summaries
- `/customer-risk`: pre-reservation customer check
- `/reservation-risk`: narrow pure no-show technical view

## Reports And Charts

The reports page includes:

- monthly no-show and cancellation trend
- channel-level high-risk concentration
- segment-level outcome view
- follow-up coverage summary
- fixed-list capture scenarios for teams that can call only the first 50, 100, or percentage-based slices

Tables remain available under the charts for audit and review.

## Demo Flow

Recommended short demo:

1. Open `/dashboard` and show the daily follow-up pool.
2. Open `/reservations` and filter by hotel, channel, risk class, or arrival date.
3. Open a reservation detail page and show the suggested follow-up steps.
4. Add or update a follow-up record when database-backed actions are enabled.
5. Open `/reports` and show trend, channel-risk, and fixed-list capture charts.
6. Open Swagger at `http://localhost:8000/docs` for the API surface.

## Acceptance Criteria

The system is acceptable when:

- H1/H2 data loads reproducibly
- raw and clean reservation records are preserved
- pure no-show and arrival failure targets are constructed correctly
- leakage-prone fields are blocked before training
- `customer_pre_reservation`, `reservation_post_booking`, and `arrival_failure_post_booking` train end to end
- `catboost_with_logistic_score` artifacts are persisted
- calibrated scores, threshold tables, fixed-list capture, feature drift, and feature percentiles are generated
- dashboard, reservation pool, detail, follow-up, and reports screens render
- risk labels and thresholds match backend constants
- tests or validation steps cover the changed behavior

## Current V1 Status

Present:

- ingestion and clean data layer
- feature generation
- temporal split
- CatBoost with Logistic Regression feeder
- isotonic calibration
- artifact persistence
- PostgreSQL schema
- dashboard and reservation pool
- reservation detail and follow-up flow
- reports with charts
- customer pre-check and pure no-show review screens
- backend dynamic tests and frontend typecheck

Still incomplete:

- production authentication and role-based access
- live scoring separated cleanly from training
- real PMS/CRM/payment/contact/campaign/deposit event data
- measured intervention outcomes
- production drift and calibration monitoring UI

## Roadmap

1. Replace synthetic operational signals with real timestamped source data.
2. Add a dedicated batch or live scoring job separate from training.
3. Persist active stage predictions to the database by default.
4. Add authentication and role-based access.
5. Track follow-up outcomes, not only action status.
6. Add drift and calibration trend monitoring.
7. Add period-over-period management reporting.
8. Revalidate thresholds after real operational data is connected.

## Out Of Scope

- generic marketing dashboards
- traffic, ROAS, CPC, CTR, or ad-spend analytics
- automated guest rejection
- guest creditworthiness scoring
- adding more model candidates without a clear product reason

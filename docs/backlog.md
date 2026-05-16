# Backlog

## Done

- Backend skeleton
- Frontend skeleton
- Docker compose
- Environment configuration
- H1/H2 ingestion
- Raw and clean reservation layers
- No-show target construction
- Canceled-row exclusion for no-show training
- Stage-aware feature policies
- Leakage guards
- Temporal split
- CatBoost training
- Logistic Regression feeder score
- Isotonic score calibration
- Threshold, top-k, calibration, drift, and percentile artifacts
- Prediction persistence model
- Dashboard
- Reservation list
- Reservation detail
- Action create / update flow
- Reports endpoints
- Customer risk UI
- Reservation risk UI

## Next

1. Replace synthetic operational signals with real source data.
2. Add a dedicated batch/live scoring job separate from training.
3. Persist active stage predictions to DB by default.
4. Add auth and role-based access.
5. Track action outcomes, not only action status.
6. Add drift and calibration trend monitoring.
7. Add period comparison to management reports.
8. Revalidate thresholds after real operational data is connected.

## Not Planned Unless Explicitly Requested

- More model candidates
- Generic marketing dashboard
- Traffic / ad spend analytics
- Multi-class cancellation/no-show/check-out modeling
- Neural tabular experiments

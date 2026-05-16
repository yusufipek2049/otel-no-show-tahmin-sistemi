# Backlog

This backlog tracks the practical path from the current proof-of-concept to a production-ready no-show operations system.

## Done

The project already includes the core V1 shape:

- backend skeleton
- frontend skeleton
- Docker Compose setup
- environment configuration
- H1/H2 ingestion
- raw and clean reservation layers
- no-show target construction
- canceled-row exclusion for no-show training
- stage-aware feature policies
- leakage guards
- temporal split
- CatBoost training
- Logistic Regression feeder score
- isotonic score calibration
- threshold, Top-K, calibration, drift, and percentile artifacts
- prediction persistence model
- dashboard
- reservation list
- reservation detail
- action create / update flow
- reports endpoints
- customer risk UI
- reservation risk UI

## Next

1. Replace synthetic operational signals with real source data.
2. Add a dedicated batch/live scoring job separate from training.
3. Persist active stage predictions to the database by default.
4. Add authentication and role-based access.
5. Track action outcomes, not only action status.
6. Add drift and calibration trend monitoring.
7. Add period comparisons to management reports.
8. Revalidate thresholds after real operational data is connected.

## Not Planned Unless Explicitly Requested

These items are intentionally outside the current path:

- adding more model candidates for its own sake
- building a generic marketing dashboard
- traffic, ad spend, ROAS, CPC, or CTR analytics
- multi-class cancellation/no-show/check-out modeling
- neural tabular experiments
